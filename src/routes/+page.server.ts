import { supabase } from '$lib/supabaseClient';
import type { JobApplication } from '$lib/types';
import type { PageServerLoad } from './$types';

/**
 * missing_skills bisa tersimpan sebagai array (jsonb) atau string JSON (text).
 * Normalisasi agar komponen selalu menerima array string.
 */
function normalizeSkills(value: unknown): string[] {
	if (Array.isArray(value)) return value.map(String);
	if (typeof value === 'string' && value.trim() !== '') {
		try {
			const parsed = JSON.parse(value);
			return Array.isArray(parsed) ? parsed.map(String) : [];
		} catch {
			return [];
		}
	}
	return [];
}

export const load: PageServerLoad = async () => {
	const { data, error } = await supabase
		.from('job_applications')
		.select('*')
		.order('match_score', { ascending: false });

	if (error) {
		console.error('Supabase error:', error.message);
		return { jobs: [] as JobApplication[] };
	}

	const jobs = ((data as JobApplication[]) ?? []).map((job) => ({
		...job,
		missing_skills: normalizeSkills(job.missing_skills)
	}));

	return { jobs };
};
