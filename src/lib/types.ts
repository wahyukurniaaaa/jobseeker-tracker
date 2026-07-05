export type ApplicationStatus = 'To Apply' | 'Applied' | 'Rejected' | 'Interview';

export interface JobApplication {
	id: string;
	company_name: string;
	job_title: string;
	job_url: string;
	match_score: number;
	missing_skills: string[] | null;
	cover_letter: string | null;
	status: ApplicationStatus;
	created_at: string;
}
