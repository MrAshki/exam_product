export type SchedulePayload = {
  start_time: string;
  end_time: string;
  duration_minutes: number;
};

export type ScheduleResult = {
  id: string;
  status: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  created_exam_tokens: number;
};

export type InvitationPayload = {
  send_to_all: boolean;
};

export type InvitationResult = {
  queued_emails: number;
};
