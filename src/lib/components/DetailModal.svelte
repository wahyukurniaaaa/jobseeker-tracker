<script lang="ts">
	import type { JobApplication } from '$lib/types';

	interface Props {
		job: JobApplication;
		onClose: () => void;
	}

	let { job, onClose }: Props = $props();

	let copied = $state(false);

	async function copyToClipboard() {
		if (!job.cover_letter) return;
		await navigator.clipboard.writeText(job.cover_letter);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) onClose();
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') onClose();
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- Backdrop -->
<div
	class="modal-backdrop"
	onclick={handleBackdropClick}
	role="dialog"
	aria-modal="true"
	tabindex="-1"
>
	<div class="modal-panel">
		<!-- Header -->
		<div class="modal-header">
			<div class="header-text">
				<h2 class="modal-title">{job.job_title}</h2>
				<p class="modal-subtitle">{job.company_name}</p>
				{#if job.location}
					<p class="modal-location">{job.location}</p>
				{/if}
			</div>
			<button class="close-btn" onclick={onClose} aria-label="Tutup">✕</button>
		</div>

		<!-- Content -->
		<div class="modal-body">
			<!-- Match + Link summary -->
			<div class="summary-row">
				<span
					class="match-num"
					class:high={job.match_score >= 80}
					class:mid={job.match_score >= 50 && job.match_score < 80}
				>
					{job.match_score}<span class="pct">%</span>
					<span class="match-label">match score</span>
				</span>
				<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
				<a href={job.job_url} target="_blank" rel="noopener noreferrer" class="open-link">
					Buka lowongan ↗
				</a>
			</div>

			<!-- Description -->
			<section class="detail-section">
				<h3 class="section-title">Deskripsi</h3>
				{#if job.job_description}
					<p class="description-text">{job.job_description}</p>
				{:else}
					<p class="empty-text">Deskripsi tidak tersedia</p>
				{/if}
			</section>

			<!-- Missing Skills -->
			<section class="detail-section">
				<h3 class="section-title">Skill yang kurang</h3>
				{#if job.missing_skills && job.missing_skills.length > 0}
					<div class="skills-container">
						{#each job.missing_skills as skill (skill)}
							<span class="skill-tag">{skill}</span>
						{/each}
					</div>
				{:else}
					<p class="empty-text">Semua skill terpenuhi</p>
				{/if}
			</section>

			<!-- Cover Letter -->
			<section class="detail-section">
				<div class="section-header-row">
					<h3 class="section-title">Cover letter</h3>
					{#if job.cover_letter}
						<button class="copy-btn" onclick={copyToClipboard} class:copied>
							{copied ? 'Tersalin' : 'Salin'}
						</button>
					{/if}
				</div>
				{#if job.cover_letter}
					<div class="cover-letter-box">
						<pre class="cover-letter-text">{job.cover_letter}</pre>
					</div>
				{:else}
					<p class="empty-text">Belum ada cover letter</p>
				{/if}
			</section>
		</div>
	</div>
</div>

<style>
	.modal-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.7);
		backdrop-filter: blur(4px);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 16px;
		animation: fadeIn 0.15s ease;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	.modal-panel {
		background: #1a1f2e;
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-radius: 16px;
		width: 100%;
		max-width: 680px;
		max-height: 85vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		animation: slideUp 0.2s ease;
		box-shadow:
			0 25px 60px rgba(0, 0, 0, 0.5),
			0 0 0 1px rgba(255, 255, 255, 0.05);
	}

	@keyframes slideUp {
		from {
			transform: translateY(20px);
			opacity: 0;
		}
		to {
			transform: translateY(0);
			opacity: 1;
		}
	}

	.modal-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		padding: 24px 28px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.07);
		flex-shrink: 0;
	}

	.header-text {
		min-width: 0;
	}

	.modal-title {
		font-size: 1.15rem;
		font-weight: 700;
		color: #f1f5f9;
		margin: 0;
		line-height: 1.3;
	}

	.modal-subtitle {
		font-size: 0.875rem;
		color: #94a3b8;
		margin: 4px 0 0 0;
	}

	.modal-location {
		font-size: 0.8rem;
		color: #64748b;
		margin: 4px 0 0 0;
	}

	.summary-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		flex-wrap: wrap;
	}

	.match-num {
		display: inline-flex;
		align-items: baseline;
		gap: 6px;
		font-size: 1.5rem;
		font-weight: 800;
		color: #ef4444;
		line-height: 1;
	}

	.match-num.mid {
		color: #eab308;
	}

	.match-num.high {
		color: #22c55e;
	}

	.match-num .pct {
		font-size: 1rem;
	}

	.match-label {
		font-size: 0.72rem;
		font-weight: 500;
		color: #64748b;
		letter-spacing: 0.02em;
	}

	.open-link {
		font-size: 0.82rem;
		font-weight: 500;
		color: #cbd5e1;
		text-decoration: none;
		border: 1px solid rgba(255, 255, 255, 0.12);
		border-radius: 8px;
		padding: 7px 13px;
		transition: all 0.15s ease;
	}

	.open-link:hover {
		background: rgba(255, 255, 255, 0.06);
		border-color: rgba(255, 255, 255, 0.2);
	}

	.description-text {
		font-size: 0.87rem;
		line-height: 1.7;
		color: #cbd5e1;
		margin: 0;
		white-space: pre-wrap;
		word-break: break-word;
	}

	.close-btn {
		background: rgba(255, 255, 255, 0.06);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		color: #94a3b8;
		width: 34px;
		height: 34px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		font-size: 1rem;
		transition: all 0.2s ease;
		flex-shrink: 0;
	}

	.close-btn:hover {
		background: rgba(255, 255, 255, 0.12);
		color: #f1f5f9;
	}

	.modal-body {
		overflow-y: auto;
		padding: 24px 28px;
		display: flex;
		flex-direction: column;
		gap: 28px;
	}

	.detail-section {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.section-title {
		font-size: 0.8rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #475569;
		margin: 0;
	}

	.section-header-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.skills-container {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}

	.skill-tag {
		background: rgba(255, 255, 255, 0.04);
		color: #cbd5e1;
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 6px;
		padding: 4px 12px;
		font-size: 0.8rem;
		font-weight: 500;
	}

	.empty-text {
		color: #64748b;
		font-size: 0.875rem;
		margin: 0;
	}

	.copy-btn {
		background: rgba(96, 165, 250, 0.1);
		border: 1px solid rgba(96, 165, 250, 0.25);
		border-radius: 8px;
		color: #60a5fa;
		padding: 5px 14px;
		font-size: 0.8rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.copy-btn:hover {
		background: rgba(96, 165, 250, 0.2);
	}

	.copy-btn.copied {
		background: rgba(34, 197, 94, 0.1);
		border-color: rgba(34, 197, 94, 0.25);
		color: #22c55e;
	}

	.cover-letter-box {
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(255, 255, 255, 0.06);
		border-radius: 10px;
		padding: 16px;
		max-height: 280px;
		overflow-y: auto;
	}

	.cover-letter-text {
		font-family:
			'Inter',
			-apple-system,
			sans-serif;
		font-size: 0.85rem;
		line-height: 1.7;
		color: #cbd5e1;
		white-space: pre-wrap;
		word-break: break-word;
		margin: 0;
	}

	.modal-body::-webkit-scrollbar,
	.cover-letter-box::-webkit-scrollbar {
		width: 4px;
	}
	.modal-body::-webkit-scrollbar-track,
	.cover-letter-box::-webkit-scrollbar-track {
		background: transparent;
	}
	.modal-body::-webkit-scrollbar-thumb,
	.cover-letter-box::-webkit-scrollbar-thumb {
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
	}
</style>
