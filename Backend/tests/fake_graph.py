"""In-memory stand-in for Neo4j used by the test-suite.

This is a MOCK. It recognises the specific Cypher statements the services
issue (matched on distinctive fragments) and applies equivalent semantics to a
set of edges. It does not parse Cypher, so it can NOT prove that the queries
are valid against a real Neo4j server.
"""
import re
from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple

from app.database.neo4j import GraphUnavailableError

Edge = Tuple[str, str, str]  # (src_user_id, rel_type, dst_id)


def _norm(q: str) -> str:
    return re.sub(r"\s+", " ", q).strip()


class FakeGraph:
    def __init__(self) -> None:
        self.edges: Set[Edge] = set()
        self.view_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        self.user_names: Dict[str, str] = {}
        self.event_nodes: Set[str] = set()
        self.available = True
        self.queries: List[str] = []

    # -- helpers ----------------------------------------------------------
    def _out(self, user: str, rels: List[str]) -> List[str]:
        return [d for (s, r, d) in self.edges if s == user and r in rels]

    def _in(self, dst: str, rel: str) -> List[str]:
        return [s for (s, r, d) in self.edges if d == dst and r == rel]

    def _following(self, user: str) -> Set[str]:
        return set(self._out(user, ["FOLLOWS"]))

    # -- entry point mirroring app.database.neo4j.execute_query ------------
    async def execute_query(self, query: str, parameters: dict = None, *, required: bool = True):
        if not self.available:
            if required:
                raise GraphUnavailableError("Graph database is unavailable.")
            return []
        q = _norm(query)
        p = parameters or {}
        self.queries.append(q)
        return self._dispatch(q, p)

    def _dispatch(self, q: str, p: Dict[str, Any]) -> List[Dict[str, Any]]:
        if q.startswith("CREATE CONSTRAINT"):
            return []

        # ---- writes: interaction edges ----
        m = re.search(r"MERGE \(u\)-\[r:(LIKED|REGISTERED|SHARED)\]->\(e\)", q)
        if m and "MERGE (u:User" in q:
            self.user_names.setdefault(p["user_id"], p.get("user_name", ""))
            self.event_nodes.add(p["event_id"])
            self.edges.add((p["user_id"], m.group(1), p["event_id"]))
            return [{"r": {}}]
        if "MERGE (u)-[r:VIEWED]->(e)" in q:
            self.edges.add((p["user_id"], "VIEWED", p["event_id"]))
            self.view_counts[(p["user_id"], p["event_id"])] += 1
            return [{"r": {}}]
        if "MERGE (u)-[r:HOSTED]->(e)" in q:
            self.edges.add((p["host_id"], "HOSTED", p["event_id"]))
            return [{"r": {}}]
        m = re.search(r"-\[r:(LIKED|REGISTERED)\]->\(e:Event \{event_id: \$event_id\}\) DELETE r", q)
        if m:
            self.edges.discard((p["user_id"], m.group(1), p["event_id"]))
            return []

        # ---- follow ----
        if "MERGE (a)-[r:FOLLOWS]->(b)" in q:
            self.edges.add((p["follower_id"], "FOLLOWS", p["target_id"]))
            return [{"r": {}}]
        if "DELETE r" in q and "FOLLOWS" in q:
            self.edges.discard((p["follower_id"], "FOLLOWS", p["target_id"]))
            return []
        if "RETURN count(r) > 0 AS is_following" in q:
            return [{"is_following": (p["follower_id"], "FOLLOWS", p["target_id"]) in self.edges}]

        # ---- user nodes ----
        if q.startswith("MERGE (u:User {user_id: $user_id}) SET u.name"):
            self.user_names[p["user_id"]] = p["name"]
            return []
        if q.startswith("MATCH (u:User {user_id: $user_id}) SET u.name"):
            self.user_names[p["user_id"]] = p["name"]
            return []

        # ---- follower / following id lists ----
        if "MATCH (f:User)-[:FOLLOWS]->(:User {user_id: $user_id}) RETURN f.user_id" in q:
            return [{"user_id": s} for (s, r, d) in self.edges if r == "FOLLOWS" and d == p["user_id"]]
        if "MATCH (:User {user_id: $user_id})-[:FOLLOWS]->(f:User) RETURN f.user_id" in q:
            return [{"user_id": x} for x in self._following(p["user_id"])]

        # ---- profile counts ----
        if "AS followers_count" in q:
            uid = p["user_id"]
            return [{
                "followers_count": len([1 for (_, r, d) in self.edges if r == "FOLLOWS" and d == uid]),
                "following_count": len(self._following(uid)),
            }]

        # ---- mutuals ----
        if "RETURN DISTINCT m.user_id AS user_id" in q:
            return [{"user_id": x} for x in self._following(p["user_id"]) & self._following(p["target_id"])]

        # ---- common interests (one row per event, like the real query) ----
        if "collect(DISTINCT type(r1)) AS my_actions" in q:
            acts = ["LIKED", "REGISTERED", "SHARED", "VIEWED"]
            mine = defaultdict(set)
            theirs = defaultdict(set)
            for (s, r, d) in self.edges:
                if r in acts and s == p["user_id"]:
                    mine[d].add(r)
                if r in acts and s == p["target_id"]:
                    theirs[d].add(r)
            return [
                {"event_id": e, "my_actions": sorted(mine[e]), "target_actions": sorted(theirs[e])}
                for e in mine if e in theirs
            ]

        # ---- suggestions: friends-of-friends ----
        if "AS mutual_count ORDER BY mutual_count DESC" in q:
            me = p["user_id"]
            mine = self._following(me)
            counts: Dict[str, int] = defaultdict(int)
            for friend in mine:
                for cand in self._following(friend):
                    if cand != me and cand not in mine:
                        counts[cand] += 1
            ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[: p["limit"]]
            return [{"user_id": u, "mutual_count": c} for u, c in ranked]

        # ---- feed ----
        if "friend.user_id AS friend_id, type(r) AS interaction_type" in q:
            acts = ["LIKED", "REGISTERED", "SHARED", "VIEWED"]
            rows = []
            for friend in self._following(p["user_id"]):
                for (s, r, d) in self.edges:
                    if s == friend and r in acts:
                        rows.append({"event_id": d, "friend_id": friend, "interaction_type": r})
            return rows

        # ---- batched list stats ----
        if q.startswith("UNWIND $event_ids AS eid"):
            rows = []
            for eid in p["event_ids"]:
                likers = self._in(eid, "LIKED")
                regs = self._in(eid, "REGISTERED")
                rows.append({
                    "event_id": eid,
                    "like_count": len(likers),
                    "registration_count": len(regs),
                    "is_liked_by_me": p["user_id"] in likers,
                    "is_registered_by_me": p["user_id"] in regs,
                })
            return rows

        # ---- single event detail stats ----
        if "AS view_count" in q and "AS share_count" in q:
            eid = p["event_id"]
            return [{
                "like_count": len(self._in(eid, "LIKED")),
                "registration_count": len(self._in(eid, "REGISTERED")),
                "view_count": len(self._in(eid, "VIEWED")),
                "share_count": len(self._in(eid, "SHARED")),
                "is_liked_by_me": p["user_id"] in self._in(eid, "LIKED"),
                "is_registered_by_me": p["user_id"] in self._in(eid, "REGISTERED"),
            }]

        # ---- registered events for a user ----
        if "-[:REGISTERED]->(e:Event) RETURN e.event_id" in q:
            return [{"event_id": d} for d in self._out(p["user_id"], ["REGISTERED"])]

        # ---- admin analytics ----
        if "RETURN count(u) AS total_users" in q:
            users = {s for (s, _, _) in self.edges} | {d for (_, r, d) in self.edges if r == "FOLLOWS"}
            return [{"total_users": len(users | set(self.user_names))}]
        if "AS total_follows" in q:
            return [{"total_follows": len([1 for (_, r, _) in self.edges if r == "FOLLOWS"])}]
        if "AS follower_count" in q:
            counts = defaultdict(int)
            for (_, r, d) in self.edges:
                if r == "FOLLOWS":
                    counts[d] += 1
            ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
            return [{"user_id": u, "name": self.user_names.get(u), "follower_count": c} for u, c in ranked]
        if "AS interaction_count" in q:
            counts = defaultdict(int)
            for (_, r, d) in self.edges:
                if r in ("LIKED", "REGISTERED", "SHARED", "VIEWED"):
                    counts[d] += 1
            ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
            return [{"event_id": e, "interaction_count": c} for e, c in ranked]

        raise AssertionError(f"FakeGraph received an unrecognised query: {q}")
