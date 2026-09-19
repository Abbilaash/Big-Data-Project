// Mock/static data for CampusConnect.
// No backend, database, or API calls — everything here is local sample data.

export type EventItem = {
  id: string
  name: string
  date: string
  time: string
  location: string
  organizer: string
  participants: number
  category: string
  description: string
  skills: string[]
}

export type Student = {
  id: string
  name: string
  department: string
  year: string
  email: string
  skills: string[]
  interests: string[]
  events: string[]
  projects: string[]
  clubs: string[]
}

// The signed-in student (used for "common skills" and the profile page).
export const currentUser: Student = {
  id: "arun",
  name: "Arun Nair",
  department: "CSE",
  year: "3rd Year",
  email: "arun.nair@campus.edu",
  skills: ["React", "MongoDB", "Node.js", "UI Design", "Python"],
  interests: ["Web Development", "Open Source", "Hackathons"],
  events: ["AI Hackathon", "Web Development Workshop"],
  projects: ["CampusConnect", "Expense Tracker App"],
  clubs: ["Coding Club", "Open Source Society"],
}

export const stats = [
  { label: "Events Registered", value: 8 },
  { label: "Events Attended", value: 5 },
  { label: "Skills", value: currentUser.skills.length },
  { label: "Connections", value: 24 },
]

export const events: EventItem[] = [
  {
    id: "ai-hackathon",
    name: "AI Hackathon",
    date: "Oct 12, 2026",
    time: "9:00 AM - 6:00 PM",
    location: "Main Auditorium",
    organizer: "Coding Club",
    participants: 120,
    category: "Hackathon",
    description:
      "A 24-hour hackathon where teams build AI-powered solutions to real campus problems. Mentors and prizes included.",
    skills: ["Python", "Machine Learning", "React"],
  },
  {
    id: "web-dev-workshop",
    name: "Web Development Workshop",
    date: "Oct 18, 2026",
    time: "2:00 PM - 5:00 PM",
    location: "Lab Block B, Room 204",
    organizer: "Web Dev Society",
    participants: 60,
    category: "Workshop",
    description:
      "Hands-on workshop covering modern web development with React, Next.js and Tailwind CSS. Beginner friendly.",
    skills: ["HTML", "CSS", "React"],
  },
  {
    id: "cloud-bootcamp",
    name: "Cloud Computing Bootcamp",
    date: "Oct 25, 2026",
    time: "10:00 AM - 4:00 PM",
    location: "Seminar Hall 1",
    organizer: "Cloud Guild",
    participants: 45,
    category: "Bootcamp",
    description:
      "Learn the fundamentals of cloud computing, deployment and DevOps with practical labs on AWS and Vercel.",
    skills: ["AWS", "Docker", "Linux"],
  },
  {
    id: "ml-seminar",
    name: "Machine Learning Seminar",
    date: "Nov 2, 2026",
    time: "11:00 AM - 1:00 PM",
    location: "Seminar Hall 2",
    organizer: "AI & DS Department",
    participants: 90,
    category: "Seminar",
    description:
      "An industry expert talk on the latest trends in machine learning, followed by an interactive Q&A session.",
    skills: ["Python", "Data Science"],
  },
  {
    id: "coding-contest",
    name: "Coding Contest",
    date: "Nov 8, 2026",
    time: "3:00 PM - 6:00 PM",
    location: "Computer Center",
    organizer: "Competitive Programming Club",
    participants: 150,
    category: "Contest",
    description:
      "A competitive programming contest with algorithmic challenges. Solve problems, climb the leaderboard, win prizes.",
    skills: ["C++", "Data Structures", "Algorithms"],
  },
  {
    id: "robotics-meetup",
    name: "Robotics Meetup",
    date: "Nov 15, 2026",
    time: "1:00 PM - 4:00 PM",
    location: "Robotics Lab",
    organizer: "Robotics Club",
    participants: 40,
    category: "Meetup",
    description:
      "Meet fellow robotics enthusiasts, showcase your projects and learn about Arduino, sensors and automation.",
    skills: ["Arduino", "C", "Electronics"],
  },
]

export const students: Student[] = [
  {
    id: "priya-sharma",
    name: "Priya Sharma",
    department: "CSE",
    year: "3rd Year",
    email: "priya.sharma@campus.edu",
    skills: ["React", "MongoDB", "UI Design"],
    interests: ["Frontend Development", "Design Systems"],
    events: ["Web Development Workshop", "AI Hackathon"],
    projects: ["Campus Food App", "Portfolio Builder"],
    clubs: ["Web Dev Society", "Design Club"],
  },
  {
    id: "karthik-kumar",
    name: "Karthik Kumar",
    department: "IT",
    year: "4th Year",
    email: "karthik.kumar@campus.edu",
    skills: ["Python", "Machine Learning", "TensorFlow"],
    interests: ["AI Research", "Data Science"],
    events: ["Machine Learning Seminar", "AI Hackathon"],
    projects: ["Face Recognition System", "Chatbot"],
    clubs: ["AI Club"],
  },
  {
    id: "rahul-verma",
    name: "Rahul Verma",
    department: "CSE",
    year: "3rd Year",
    email: "rahul.verma@campus.edu",
    skills: ["Java", "Spring Boot", "SQL"],
    interests: ["Backend Development", "System Design"],
    events: ["Coding Contest", "Cloud Computing Bootcamp"],
    projects: ["Library Management System", "REST API Gateway"],
    clubs: ["Competitive Programming Club"],
  },
  {
    id: "ananya-rao",
    name: "Ananya Rao",
    department: "AI&DS",
    year: "2nd Year",
    email: "ananya.rao@campus.edu",
    skills: ["Python", "Data Science", "Pandas"],
    interests: ["Data Visualization", "Statistics"],
    events: ["Machine Learning Seminar"],
    projects: ["Sales Dashboard", "Weather Predictor"],
    clubs: ["AI & DS Department", "Data Club"],
  },
  {
    id: "sneha-nair",
    name: "Sneha Nair",
    department: "ECE",
    year: "3rd Year",
    email: "sneha.nair@campus.edu",
    skills: ["Arduino", "C", "Electronics"],
    interests: ["Robotics", "IoT"],
    events: ["Robotics Meetup"],
    projects: ["Smart Home System", "Line Follower Robot"],
    clubs: ["Robotics Club"],
  },
  {
    id: "vikram-singh",
    name: "Vikram Singh",
    department: "IT",
    year: "4th Year",
    email: "vikram.singh@campus.edu",
    skills: ["AWS", "Docker", "Node.js"],
    interests: ["Cloud", "DevOps"],
    events: ["Cloud Computing Bootcamp", "Coding Contest"],
    projects: ["CI/CD Pipeline", "Serverless Blog"],
    clubs: ["Cloud Guild"],
  },
]

// Simple helper: skills shared between a student and the current user.
export function commonSkills(student: Student): string[] {
  return student.skills.filter((skill) => currentUser.skills.includes(skill))
}

export const departments = ["All", "CSE", "IT", "AI&DS", "ECE"]

export const categories = [
  "All",
  "Hackathon",
  "Workshop",
  "Bootcamp",
  "Seminar",
  "Contest",
  "Meetup",
]

// All unique skills across students (used for the teammate skill filter).
export const allSkills = Array.from(
  new Set(students.flatMap((s) => s.skills)),
).sort()

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase()
}
