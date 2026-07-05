export type ApplicationStatus = 'To Apply' | 'Applied' | 'Rejected' | 'Interview';

export interface JobApplication {
	id: string;
	company_name: string;
	job_title: string;
	job_url: string;
	job_description: string | null;
	location: string | null;
	match_score: number;
	missing_skills: string[] | null;
	cover_letter: string | null;
	status: ApplicationStatus;
	created_at: string;
}

// Area lokasi yang diprioritaskan (selaras dengan scraper).
export const PREFERRED_LOCATIONS = [
	'Depok',
	'Jakarta Selatan',
	'Jakarta Pusat',
	'Jakarta Timur'
] as const;

/** True jika lokasi termasuk area prioritas. */
export function isPreferredLocation(location: string | null | undefined): boolean {
	if (!location) return false;
	const loc = location.toLowerCase();
	return PREFERRED_LOCATIONS.some((area) => loc.includes(area.toLowerCase()));
}

/** Tentukan sumber lowongan dari domain job_url. */
export function getJobSource(jobUrl: string | null | undefined): string {
	if (!jobUrl) return 'Lainnya';
	const url = jobUrl.toLowerCase();
	if (url.includes('kalibrr.com')) return 'Kalibrr';
	if (url.includes('glints.com')) return 'Glints';
	if (url.includes('jobstreet.com')) return 'JobStreet';
	if (url.includes('linkedin.com')) return 'LinkedIn';
	return 'Lainnya';
}
