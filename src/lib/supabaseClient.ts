import { createClient } from '@supabase/supabase-js';
import { env } from '$env/dynamic/public';

export const supabase = createClient(
	env.PUBLIC_SUPABASE_URL || 'https://placeholder-project.supabase.co',
	env.PUBLIC_SUPABASE_ANON_KEY || 'placeholder-anon-key'
);
