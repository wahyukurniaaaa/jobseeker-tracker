<script lang="ts">
	import type { PageData } from './$types';
	import type { ApplicationStatus, JobApplication } from '$lib/types';
	import JobCard from '$lib/components/JobCard.svelte';

	let { data }: { data: PageData } = $props();

	// ─── State ────────────────────────────────────────────────────────────────
	let jobs = $state<JobApplication[]>(data.jobs);
	let searchQuery = $state('');
	let filterStatus = $state<ApplicationStatus | 'All'>('All');
	let viewMode = $state<'grid' | 'list'>('grid');

	// ─── Derived ──────────────────────────────────────────────────────────────
	let filtered = $derived(
		jobs.filter((j) => {
			const matchesSearch =
				searchQuery === '' ||
				j.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
				j.job_title.toLowerCase().includes(searchQuery.toLowerCase());
			const matchesStatus = filterStatus === 'All' || j.status === filterStatus;
			return matchesSearch && matchesStatus;
		})
	);

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
	<title>Job Tracker — Dashboard</title>
	<meta name="description" content="Dashboard untuk melacak dan mengelola lamaran kerja otomatis" />
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link
		href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
		rel="stylesheet"
	/>
</svelte:head>

<div class="app-shell">
	<!-- Sidebar -->
	<aside class="sidebar">
		<div class="brand">
			<div class="brand-icon">🎯</div>
			<div>
				<h1 class="brand-name">JobTracker</h1>
				<p class="brand-tagline">Auto Apply Dashboard</p>
			</div>
		</div>

		<nav class="sidebar-nav">
			<a href="/" class="nav-item active">
				<span class="nav-icon">📊</span>
				Dashboard
			</a>
		</nav>

		<!-- Stats Cards -->
		<div class="stats-grid">
			<div class="stat-card">
				<span class="stat-value">{stats.total}</span>
				<span class="stat-label">Total Lamaran</span>
			</div>
			<div class="stat-card stat-blue">
				<span class="stat-value">{stats.applied}</span>
				<span class="stat-label">Applied</span>
			</div>
			<div class="stat-card stat-violet">
				<span class="stat-value">{stats.interview}</span>
				<span class="stat-label">Interview</span>
			</div>
			<div class="stat-card stat-green">
				<span class="stat-value">{stats.avgScore}%</span>
				<span class="stat-label">Avg. Match</span>
			</div>
		</div>
	</aside>

	<!-- Main Content -->
	<main class="main-content">
		<!-- Header -->
		<header class="page-header">
			<div>
				<h2 class="page-title">Lamaran Saya</h2>
				<p class="page-subtitle">
					Menampilkan <strong>{filtered.length}</strong> dari {jobs.length} lamaran
				</p>
			</div>
			<!-- View Toggle -->
			<div class="view-toggle">
				<button
					class="toggle-btn"
					class:active={viewMode === 'grid'}
					onclick={() => (viewMode = 'grid')}
					title="Grid view"
				>
					⊞
				</button>
				<button
					class="toggle-btn"
					class:active={viewMode === 'list'}
					onclick={() => (viewMode = 'list')}
					title="List view"
				>
					☰
				</button>
			</div>
		</header>

		<!-- Filter & Search Bar -->
		<div class="toolbar">
			<div class="search-wrapper">
				<span class="search-icon">🔍</span>
				<input
					class="search-input"
					type="text"
					placeholder="Cari perusahaan atau posisi..."
					bind:value={searchQuery}
				/>
			</div>

			<div class="filter-chips">
				{#each statusOptions as opt}
					<button
						class="chip"
						class:chip-active={filterStatus === opt}
						onclick={() => (filterStatus = opt)}
					>
						{opt === 'All' ? '✦ Semua' : opt}
					</button>
				{/each}
			</div>
		</div>

		<!-- Content Area -->
		{#if filtered.length === 0}
			<div class="empty-state">
				<div class="empty-icon">🗂️</div>
				<h3 class="empty-title">Tidak ada lamaran ditemukan</h3>
				<p class="empty-desc">
					{searchQuery || filterStatus !== 'All'
						? 'Coba ubah filter atau kata kunci pencarian'
						: 'Belum ada data lamaran. Cek koneksi Supabase dan pastikan tabel job_applications sudah terisi.'}
				</p>
			</div>
		{:else if viewMode === 'grid'}
			<div class="jobs-grid">
				{#each filtered as job (job.id)}
					<JobCard {job} onStatusUpdate={handleStatusUpdate} />
				{/each}
			</div>
		{:else}
			<!-- List View Table -->
			<div class="table-wrapper">
				<table class="jobs-table">
					<thead>
						<tr>
							<th>Perusahaan</th>
							<th>Posisi</th>
							<th>Match Score</th>
							<th>Status</th>
							<th>Tanggal</th>
							<th>Aksi</th>
						</tr>
					</thead>
					<tbody>
						{#each filtered as job (job.id)}
							<tr class="table-row">
								<td>
									<div class="table-company">
										<div class="mini-avatar">
											{job.company_name.charAt(0)}
										</div>
										<span class="company-text">{job.company_name}</span>
									</div>
								</td>
								<td class="title-cell">{job.job_title}</td>
								<td>
									<div class="score-cell">
										<div class="score-mini-bar">
											<div
												class="score-fill"
												style="width: {job.match_score}%; background: {job.match_score >= 80
													? '#22c55e'
													: job.match_score >= 50
														? '#eab308'
														: '#ef4444'}"
											></div>
										</div>
										<span class="score-num">{job.match_score}%</span>
									</div>
								</td>
								<td>
									<span
										class="status-pill status-{job.status.toLowerCase().replace(' ', '-')}"
									>
										{job.status}
									</span>
								</td>
								<td class="date-cell">
									{new Date(job.created_at).toLocaleDateString('id-ID', {
										day: 'numeric',
										month: 'short'
									})}
								</td>
								<td>
									<a
										href={job.job_url}
										target="_blank"
										rel="noopener noreferrer"
										class="table-link"
									>
										Lihat ↗
									</a>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
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

	.app-shell {
		display: flex;
		min-height: 100vh;
	}

	/* ─── Sidebar ─────────────────────────────────────────────────────────── */
	.sidebar {
		width: 260px;
		flex-shrink: 0;
		background: #13171f;
		border-right: 1px solid rgba(255, 255, 255, 0.06);
		padding: 28px 20px;
		display: flex;
		flex-direction: column;
		gap: 32px;
		position: sticky;
		top: 0;
		height: 100vh;
		overflow-y: auto;
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.brand-icon {
		width: 44px;
		height: 44px;
		background: linear-gradient(135deg, #1d4ed8, #7c3aed);
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.4rem;
		flex-shrink: 0;
	}

	.brand-name {
		font-size: 1.05rem;
		font-weight: 800;
		color: #f1f5f9;
		margin: 0;
		letter-spacing: -0.02em;
	}

	.brand-tagline {
		font-size: 0.7rem;
		color: #475569;
		margin: 2px 0 0;
	}

	.sidebar-nav {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.nav-item {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 10px 12px;
		border-radius: 10px;
		color: #64748b;
		text-decoration: none;
		font-size: 0.875rem;
		font-weight: 500;
		transition: all 0.2s ease;
	}

	.nav-item:hover,
	.nav-item.active {
		background: rgba(96, 165, 250, 0.1);
		color: #60a5fa;
	}

	.nav-icon {
		font-size: 1rem;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 10px;
	}

	.stat-card {
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(255, 255, 255, 0.06);
		border-radius: 12px;
		padding: 14px;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.stat-blue {
		border-color: rgba(96, 165, 250, 0.2);
		background: rgba(96, 165, 250, 0.05);
	}

	.stat-violet {
		border-color: rgba(167, 139, 250, 0.2);
		background: rgba(167, 139, 250, 0.05);
	}

	.stat-green {
		border-color: rgba(34, 197, 94, 0.2);
		background: rgba(34, 197, 94, 0.05);
	}

	.stat-value {
		font-size: 1.5rem;
		font-weight: 800;
		color: #f1f5f9;
		line-height: 1;
	}

	.stat-label {
		font-size: 0.7rem;
		color: #475569;
		font-weight: 500;
	}

	/* ─── Main Content ────────────────────────────────────────────────────── */
	.main-content {
		flex: 1;
		padding: 32px;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 24px;
	}

	.page-header {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
	}

	.page-title {
		font-size: 1.5rem;
		font-weight: 800;
		color: #f1f5f9;
		margin: 0;
		letter-spacing: -0.02em;
	}

	.page-subtitle {
		font-size: 0.85rem;
		color: #475569;
		margin: 6px 0 0;
	}

	.page-subtitle strong {
		color: #94a3b8;
	}

	.view-toggle {
		display: flex;
		background: rgba(255, 255, 255, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-radius: 10px;
		padding: 3px;
		gap: 2px;
	}

	.toggle-btn {
		width: 34px;
		height: 34px;
		border: none;
		border-radius: 7px;
		background: transparent;
		color: #475569;
		font-size: 1rem;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.toggle-btn.active {
		background: rgba(96, 165, 250, 0.15);
		color: #60a5fa;
	}

	/* ─── Toolbar ─────────────────────────────────────────────────────────── */
	.toolbar {
		display: flex;
		flex-direction: column;
		gap: 14px;
	}

	.search-wrapper {
		position: relative;
	}

	.search-icon {
		position: absolute;
		left: 14px;
		top: 50%;
		transform: translateY(-50%);
		font-size: 0.9rem;
	}

	.search-input {
		width: 100%;
		background: rgba(255, 255, 255, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-radius: 10px;
		padding: 12px 16px 12px 42px;
		color: #e2e8f0;
		font-size: 0.875rem;
		font-family: inherit;
		outline: none;
		transition: border-color 0.2s ease;
		box-sizing: border-box;
	}

	.search-input::placeholder {
		color: #475569;
	}

	.search-input:focus {
		border-color: rgba(96, 165, 250, 0.4);
		background: rgba(96, 165, 250, 0.04);
	}

	.filter-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}

	.chip {
		background: rgba(255, 255, 255, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-radius: 999px;
		padding: 5px 14px;
		font-size: 0.8rem;
		font-weight: 500;
		color: #64748b;
		cursor: pointer;
		transition: all 0.2s ease;
		font-family: inherit;
	}

	.chip:hover {
		background: rgba(255, 255, 255, 0.08);
		color: #94a3b8;
	}

	.chip-active {
		background: rgba(96, 165, 250, 0.15);
		border-color: rgba(96, 165, 250, 0.4);
		color: #60a5fa;
		font-weight: 600;
	}

	/* ─── Grid ────────────────────────────────────────────────────────────── */
	.jobs-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 16px;
	}

	/* ─── Empty State ─────────────────────────────────────────────────────── */
	.empty-state {
		text-align: center;
		padding: 80px 20px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 12px;
	}

	.empty-icon {
		font-size: 3.5rem;
	}

	.empty-title {
		font-size: 1.1rem;
		font-weight: 700;
		color: #94a3b8;
		margin: 0;
	}

	.empty-desc {
		font-size: 0.875rem;
		color: #475569;
		max-width: 360px;
		line-height: 1.6;
		margin: 0;
	}

	/* ─── Table ───────────────────────────────────────────────────────────── */
	.table-wrapper {
		border: 1px solid rgba(255, 255, 255, 0.07);
		border-radius: 14px;
		overflow: hidden;
		overflow-x: auto;
	}

	.jobs-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}

	.jobs-table th {
		background: rgba(255, 255, 255, 0.03);
		padding: 14px 18px;
		text-align: left;
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: #475569;
		border-bottom: 1px solid rgba(255, 255, 255, 0.07);
		white-space: nowrap;
	}

	.table-row td {
		padding: 16px 18px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.04);
		color: #cbd5e1;
		vertical-align: middle;
	}

	.table-row:last-child td {
		border-bottom: none;
	}

	.table-row:hover td {
		background: rgba(255, 255, 255, 0.02);
	}

	.table-company {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.mini-avatar {
		width: 30px;
		height: 30px;
		border-radius: 7px;
		background: linear-gradient(135deg, #1e40af, #4f46e5);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.8rem;
		font-weight: 700;
		color: white;
		flex-shrink: 0;
	}

	.company-text {
		font-weight: 600;
		color: #e2e8f0;
	}

	.title-cell {
		color: #94a3b8;
	}

	.score-cell {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.score-mini-bar {
		width: 60px;
		height: 5px;
		background: rgba(255, 255, 255, 0.08);
		border-radius: 3px;
		overflow: hidden;
		flex-shrink: 0;
	}

	.score-fill {
		height: 100%;
		border-radius: 3px;
		transition: width 0.4s ease;
	}

	.score-num {
		font-weight: 600;
		font-size: 0.8rem;
		color: #94a3b8;
	}

	.status-pill {
		padding: 3px 10px;
		border-radius: 999px;
		font-size: 0.75rem;
		font-weight: 600;
		white-space: nowrap;
	}

	.status-to-apply {
		background: rgba(148, 163, 184, 0.1);
		color: #94a3b8;
	}

	.status-applied {
		background: rgba(96, 165, 250, 0.1);
		color: #60a5fa;
	}

	.status-interview {
		background: rgba(167, 139, 250, 0.1);
		color: #a78bfa;
	}

	.status-rejected {
		background: rgba(248, 113, 113, 0.1);
		color: #f87171;
	}

	.date-cell {
		color: #475569;
		font-size: 0.8rem;
	}

	.table-link {
		color: #60a5fa;
		text-decoration: none;
		font-size: 0.8rem;
		font-weight: 600;
		transition: color 0.2s;
	}

	.table-link:hover {
		color: #93c5fd;
	}

	/* ─── Responsive ──────────────────────────────────────────────────────── */
	@media (max-width: 768px) {
		.app-shell {
			flex-direction: column;
		}

		.sidebar {
			width: 100%;
			height: auto;
			position: static;
			padding: 20px 16px;
			gap: 20px;
			border-right: none;
			border-bottom: 1px solid rgba(255, 255, 255, 0.06);
		}

		.stats-grid {
			grid-template-columns: repeat(4, 1fr);
		}

		.main-content {
			padding: 20px 16px;
		}

		.jobs-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
