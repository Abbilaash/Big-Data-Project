"""
Quick test script to verify:
1. Neo4j AuraDB cloud connection works
2. MongoDB local connection works (or shows clear error if not installed)

Run from Backend/ folder:
    python test_connections.py
"""
import asyncio


async def test_neo4j():
    print("\n" + "="*50)
    print("TEST 1: Neo4j AuraDB Cloud Connection")
    print("="*50)
    try:
        from neo4j import AsyncGraphDatabase
        driver = AsyncGraphDatabase.driver(
            "neo4j+s://86963e96.databases.neo4j.io",
            auth=("86963e96", "sA1X3prkiahm_K_6VOWY8Nt-e5kaicdWsUYpnn1P_T8")
        )
        await driver.verify_connectivity()
        print("[OK] Neo4j AuraDB: CONNECTED SUCCESSFULLY")

        async with driver.session() as session:
            # Count all nodes by label
            result = await session.run(
                "MATCH (n) RETURN labels(n) AS label, count(*) AS cnt"
            )
            rows = await result.data()
            if rows:
                print("\n[DATA] Nodes in Neo4j graph:")
                for row in rows:
                    print(f"   {row['label']}: {row['cnt']} nodes")
            else:
                print("   (Graph is empty - no nodes yet)")

            # Count relationships
            rel_result = await session.run(
                "MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS cnt"
            )
            rel_rows = await rel_result.data()
            if rel_rows:
                print("\n[DATA] Relationships in Neo4j:")
                for row in rel_rows:
                    print(f"   {row['rel']}: {row['cnt']} relationships")
            else:
                print("   (No relationships yet)")

        await driver.close()

    except Exception as e:
        print("[FAIL] Neo4j connection FAILED:", e)
        print("   Check: Is the AuraDB instance active? Are credentials correct?")


async def test_mongodb():
    print("\n" + "="*50)
    print("TEST 2: MongoDB Connection")
    print("="*50)
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(
            "mongodb://localhost:27017",
            serverSelectionTimeoutMS=3000
        )
        await client.admin.command('ping')
        print("[OK] MongoDB LOCAL: CONNECTED SUCCESSFULLY")

        db = client["campusconnect"]
        users_count  = await db.users.count_documents({})
        events_count = await db.events.count_documents({})
        print("\n[DATA] Data in MongoDB (campusconnect database):")
        print(f"   users collection:  {users_count} documents")
        print(f"   events collection: {events_count} documents")
        client.close()

    except Exception as e:
        print("[FAIL] MongoDB LOCAL connection FAILED:", e)
        print("\n   MongoDB is not installed locally.")
        print("   SOLUTION: Use MongoDB Atlas (free cloud):")
        print("      1. Go to https://cloud.mongodb.com")
        print("      2. Sign up free -> Create M0 (free) cluster")
        print("      3. Create database user -> get connection string")
        print("      4. Replace MONGO_URI in Backend/.env with the Atlas URI")
        print("      5. Looks like: mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/")


async def main():
    print("\n[INFO] CampusConnect - Database Connection Test")
    await test_neo4j()
    await test_mongodb()
    print("\n" + "="*50)
    print("Test complete.")
    print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
