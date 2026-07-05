<script lang="ts">
	import type { PageData } from './$types';
	import type { ApplicationStatus, JobApplication } from '$lib/types';
	import { isPreferredLocation } from '$lib/types';
	import JobCard from '$lib/components/JobCard.svelte';

	let { data }: { data: PageData } = $props();

	// ─── State ────────────────────────────────────────────────────────────────
	let jobs = $state<JobApplication[]>(data.jobs);
	let searchQuery = $state('');
	let filterStatus = $state<ApplicationStatus | 'All'>('All');
	let onlyPreferred = $state(false);

	// ─── Derived ──────────────────────────────────────────────────────────────
	let filtered = $derived.by(() => {
		const q = searchQuery.trim().toLowerCase();
		const list = jobs.filter((j) => {
			const matchesSearch =
				q === '' ||
				j.company_name.toLowerCase().includes(q) ||
				j.job_title.toLowerCase().includes(q) ||
				(j.location ?? '').toLowerCase().includes(q);
			const matchesStatus = filterStatus === 'All' || j.status === filterStatus;
			const matchesLocation = !onlyPreferred || isPreferredLocation(j.location);
			return matchesSearch && matchesStatus && matchesLocation;
		});

		// Area prioritas selalu didahulukan, lalu urut berdasarkan match score.
		return list.sort((a, b) => {
			const pa = isPreferredLocation(a.location) ? 0 : 1;
			const pb = isPreferredLocation(b.location) ? 0 : 1;
			if (pa !== pb) return pa - pb;
			return b.match_score - a.match_score;
		});
	});

	const stats = $derived({
		total: jobs.length,
		applied: jobs.filter((j) => j.status === 'Applied').length,
		interview: jobs.filter((j) => j.status === 'Interview').length,
		avgScore:
			jobs.length > 0 ? Math.round(jobs.reduce((a, b) => a + b.match_score, 0) / jobs.length) : 0
	});

	const statusOptions: (ApplicationStatus | 'All')[] = [
		'All',
		'To Apply',
		'Applied',
		'Interview',
		'Rejected'
	];

	// ─── Handlers ─────────────────────────────────────────────────────────────
	function handleStatusUpdate(id: string, newStatus: ApplicationStatus) {
		jobs = jobs.map((j) => (j.id === id ? { ...j, status: newStatus } : j));
	}
</script>

<svelte:head>
	<title>JobTracker</title>
	<meta name="description" content="Dashboard untuk melacak dan mengelola lamaran kerja" />
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link
		href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
		rel="stylesheet"
	/>
</svelte:head>

<div class="page">
	<header class="topbar">
		<div class="brand">
			<span class="brand-mark">JT</span>
			<div>
				<h1 class="brand-name">JobTracker</h1>
				<p class="brand-tag">Lamaran kerja</p>
			</div>
		</div>
	</header>

	<main class="content">
		<!-- Stats -->
		<section class="stats" aria-label="Ringkasan">
			<div class="stat">
				<span class="stat-value">{stats.total}</span>
				<span class="stat-label">Total</span>
			</div>
			<div class="stat">
				<span class="stat-value">{stats.applied}</span>
				<span class="stat-label">Applied</span>
			</div>
			<div class="stat">
				<span class="stat-value">{stats.interview}</span>
				<span class="stat-label">Interview</span>
			</div>
			<div class="stat">
				<span class="stat-value">{stats.avgScore}%</span>
				<span class="stat-label">Avg. match</span>
			</div>
		</section>

		<!-- Toolbar -->
		<section class="toolbar">
			<div class="search">
				<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
					<path
						fill="currentColor"
						d="M15.5 14h-.79l-.28-.27a6.5 6.5 0 1 0-.7.7l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14z"
					/>
				</svg>
				<input
					type="text"
					placeholder="Cari posisi, perusahaan, atau lokasi"
					bind:value={searchQuery}
				/>
			</div>

			<div class="chips">
				{#each statusOptions as opt (opt)}
					<button
						class="chip"
						class:active={filterStatus === opt}
						onclick={() => (filterStatus = opt)}
					>
						{opt === 'All' ? 'Semua' : opt}
					</button>
				{/each}
			</div>

			<label class="loc-toggle">
				<input type="checkbox" bind:checked={onlyPreferred} />
				<span>Hanya area pilihan (Depok, Jakarta Sel/Pus/Tim)</span>
			</label>
		</section>

		<!-- Result count -->
		<p class="result-count">
			{filtered.length} dari {jobs.length} lamaran
		</p>

		<!-- Jobs -->
		{#if filtered.length === 0}
			<div class="empty">
				<h3>Tidak ada lamaran</h3>
				<p>
					{searchQuery || filterStatus !== 'All'
						? 'Coba ubah kata kunci atau filter.'
						: 'Belum ada data. Pastikan tabel job_applications di Supabase sudah terisi.'}
				</p>
			</div>
		{:else}
			<div class="jobs">
				{#each filtered as job (job.id)}
					<JobCard {job} onStatusUpdate={handleStatusUpdate} />
				{/each}
			</div>
		{/if}
	</main>
</div>

<style>
	:global(body) {
		font-family:
			'Inter',
			-apple-system,
			BlinkMacSystemFont,
			sans-serif;
		background: #0f1117;
		color: #e2e8f0;
		margin: 0;
	}

	.page {
		max-width: 1100px;
		margin: 0 auto;
		min-height: 100vh;
	}

	/* ─── Topbar ───────────────────────────────────────────────────────────── */
	.topbar {
		position: sticky;
		top: 0;
		z-index: 10;
		background: rgba(15, 17, 23, 0.85);
		backdrop-filter: blur(8px);
		border-bottom: 1px solid rgba(255, 255, 255, 0.06);
		padding: 14px 16px;
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 11px;
	}

	.brand-mark {
		width: 38px;
		height: 38px;
		border-radius: 10px;
		background: #232a3a;
		border: 1px solid rgba(255, 255, 255, 0.1);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.85rem;
		font-weight: 800;
		color: #e2e8f0;
		letter-spacing: 0.02em;
	}

	.brand-name {
		font-size: 1rem;
		font-weight: 700;
		color: #f1f5f9;
		margin: 0;
		line-height: 1.1;
	}

	.brand-tag {
		font-size: 0.72rem;
		color: #64748b;
		margin: 2px 0 0;
	}

	/* ─── Content ──────────────────────────────────────────────────────────── */
	.content {
		padding: 16px;
		display: flex;
		flex-direction: column;
		gap: 18px;
	}

	/* ─── Stats ────────────────────────────────────────────────────────────── */
	.stats {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 10px;
	}

	.stat {
		background: #161b27;
		border: 1px solid rgba(255, 255, 255, 0.07);
		border-radius: 12px;
		padding: 13px 15px;
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	.stat-value {
		font-size: 1.35rem;
		font-weight: 800;
		color: #f1f5f9;
		line-height: 1;
	}

	.stat-label {
		font-size: 0.72rem;
		color: #64748b;
	}

	/* ─── Toolbar ──────────────────────────────────────────────────────────── */
	.toolbar {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.search {
		position: relative;
		display: flex;
		align-items: center;
	}

	.search svg {
		position: absolute;
		left: 13px;
		color: #64748b;
		pointer-events: none;
	}

	.search input {
		width: 100%;
		background: #161b27;
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-radius: 10px;
		padding: 11px 14px 11px 38px;
		color: #e2e8f0;
		font-size: 0.875rem;
		font-family: inherit;
		outline: none;
		transition: border-color 0.15s ease;
		box-sizing: border-box;
	}

	.search input::placeholder {
		color: #64748b;
	}

	.search input:focus {
		border-color: rgba(255, 255, 255, 0.2);
	}

	.chips {
		display: flex;
		gap: 8px;
		overflow-x: auto;
		padding-bottom: 2px;
		scrollbar-width: none;
	}

	.chips::-webkit-scrollbar {
		display: none;
	}

	.chip {
		background: #161b27;
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-radius: 999px;
		padding: 6px 14px;
		font-size: 0.8rem;
		font-weight: 500;
		color: #94a3b8;
		cursor: pointer;
		transition: all 0.15s ease;
		font-family: inherit;
		white-space: nowrap;
		flex-shrink: 0;
	}

	.chip:hover {
		border-color: rgba(255, 255, 255, 0.18);
		color: #cbd5e1;
	}

	.chip.active {
		background: #e2e8f0;
		border-color: #e2e8f0;
		color: #0f1117;
		font-weight: 600;
	}

	.loc-toggle {
		display: flex;
		align-items: center;
		gap: 9px;
		font-size: 0.8rem;
		color: #94a3b8;
		cursor: pointer;
		user-select: none;
	}

	.loc-toggle input {
		width: 16px;
		height: 16px;
		accent-color: #34d399;
		cursor: pointer;
	}

	/* ─── Result count ─────────────────────────────────────────────────────── */
	.result-count {
		font-size: 0.8rem;
		color: #64748b;
		margin: 0;
	}

	/* ─── Jobs ─────────────────────────────────────────────────────────────── */
	.jobs {
		display: grid;
		grid-template-columns: 1fr;
		gap: 12px;
	}

	/* ─── Empty ────────────────────────────────────────────────────────────── */
	.empty {
		text-align: center;
		padding: 60px 20px;
		border: 1px dashed rgba(255, 255, 255, 0.1);
		border-radius: 14px;
	}

	.empty h3 {
		font-size: 1rem;
		font-weight: 600;
		color: #cbd5e1;
		margin: 0 0 8px;
	}

	.empty p {
		font-size: 0.85rem;
		color: #64748b;
		max-width: 340px;
		margin: 0 auto;
		line-height: 1.6;
	}

	/* ─── Tablet / Desktop ─────────────────────────────────────────────────── */
	@media (min-width: 640px) {
		.topbar {
			padding: 16px 24px;
		}

		.content {
			padding: 24px;
			gap: 22px;
		}

		.stats {
			grid-template-columns: repeat(4, 1fr);
		}

		.toolbar {
			display: grid;
			grid-template-columns: 1fr auto;
			align-items: center;
			gap: 12px 16px;
		}

		.search {
			grid-column: 1 / -1;
		}

		.loc-toggle {
			justify-self: end;
		}
	}

	@media (min-width: 900px) {
		.jobs {
			grid-template-columns: repeat(2, 1fr);
			gap: 14px;
		}
	}
</style>
