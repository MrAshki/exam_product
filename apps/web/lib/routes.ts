export const routes = {
  home: "/",
  login: "/login",
  register: "/register",
  dashboard: "/dashboard",
  classDetail: (classId: string) => `/dashboard/classes/${classId}`,
  classStudents: (classId: string) => `/dashboard/classes/${classId}/students`,
  classExams: (classId: string) => `/dashboard/classes/${classId}/exams`,
  examBuilder: (classId: string, examId: string) =>
    `/dashboard/classes/${classId}/exams/${examId}/builder`,
  examSchedule: (classId: string, examId: string) =>
    `/dashboard/classes/${classId}/exams/${examId}/schedule`,
  examReview: (classId: string, examId: string) =>
    `/dashboard/classes/${classId}/exams/${examId}/review`,
  appeals: (classId: string) => `/dashboard/classes/${classId}/appeals`,
  appealDetail: (classId: string, appealId: string) =>
    `/dashboard/classes/${classId}/appeals/${appealId}`,
  studentExam: (examToken: string) => `/exam/access/${examToken}`,
  result: (resultToken: string) => `/result/${resultToken}`,
  leaderboard: (leaderboardToken: string) => `/leaderboard/${leaderboardToken}`
};
