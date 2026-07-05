import { supabase } from '$lib/supabaseClient';
import type { JobApplication } from '$lib/types';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
	const { data, error } = await supabase
		.from('job_applications')
		.select('*')
		.order('match_score', { ascending: false });

	if (error) {
		console.error('Supabase error:', error.message);
		return { jobs: [] as JobApplication[] };
	}

	return { jobs: (data as JobApplication[]) ?? [] };
};
