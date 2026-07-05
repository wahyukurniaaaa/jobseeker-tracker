<script lang="ts">
	import type { JobApplication, ApplicationStatus } from '$lib/types';
	import MatchBadge from './MatchBadge.svelte';
	import StatusDropdown from './StatusDropdown.svelte';
	import DetailModal from './DetailModal.svelte';

	interface Props {
		job: JobApplication;
		onStatusUpdate?: (id: string, newStatus: ApplicationStatus) => void;
	}

	let { job, onStatusUpdate }: Props = $props();

	let showModal = $state(false);
	let currentJob = $state({ ...job });

	function handleStatusUpdate(id: string, newStatus: ApplicationStatus) {
		currentJob = { ...currentJob, status: newStatus };
		onStatusUpdate?.(id, newStatus);
	}

	const formatDate = (dateStr: string) => {
		return new Date(dateStr).toLocaleDateString('id-ID', {
			day: 'numeric',
			month: 'short',
			year: 'numeric'
		});
	};
</script>

<div class="job-card">
	<!-- Score bar accent -->
	<div
		class="score-bar"
		style="width: {currentJob.match_score}%; background: {currentJob.match_score >= 80
			? '#22c55e'
			: currentJob.match_score >= 50
				? '#eab308'
				: '#ef4444'}"
	></div>

	<div class="card-content">
		<!-- Top row -->
		<div class="card-top">
			<div class="company-info">
				<div class="company-avatar">
					{currentJob.company_name.charAt(0).toUpperCase()}
				</div>
				<div>
					<h3 class="company-name">{currentJob.company_name}</h3>
					<p class="job-title">{currentJob.job_title}</p>
				</div>
			</div>
			<MatchBadge score={currentJob.match_score} />
		</div>

		<!-- Meta row -->
		<div class="card-meta">
			<span class="meta-date">📅 {formatDate(currentJob.created_at)}</span>
			{#if currentJob.missing_skills && currentJob.missing_skills.length > 0}
				<span class="meta-skills">⚠️ {currentJob.missing_skills.length} skill missing</span>
			{/if}
		</div>

		<!-- Bottom row -->
		<div class="card-bottom">
			<StatusDropdown
				id={currentJob.id}
				bind:status={currentJob.status}
				onUpdate={handleStatusUpdate}
			/>
			<button class="details-btn" onclick={() => (showModal = true)}>
				Detail <span>→</span>
			</button>
		</div>
	</div>
</div>

{#if showModal}
	<DetailModal job={currentJob} onClose={() => (showModal = false)} />
{/if}

<style>
	.job-card {
		background: linear-gradient(135deg, #1a1f2e 0%, #161b27 100%);
		border: 1px solid rgba(255, 255, 255, 0.07);
		border-radius: 14px;
		overflow: hidden;
		transition:
			transform 0.2s ease,
			box-shadow 0.2s ease,
			border-color 0.2s ease;
		position: relative;
	}

	.job-card:hover {
		transform: translateY(-3px);
		border-color: rgba(96, 165, 250, 0.25);
		box-shadow:
			0 12px 40px rgba(0, 0, 0, 0.3),
			0 0 0 1px rgba(96, 165, 250, 0.1);
	}

	.score-bar {
		height: 3px;
		transition: width 0.6s ease;
	}

	.card-content {
		padding: 20px;
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.card-top {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 12px;
	}

	.company-info {
		display: flex;
		align-items: center;
		gap: 12px;
		min-width: 0;
	}

	.company-avatar {
		width: 42px;
		height: 42px;
		border-radius: 10px;
		background: linear-gradient(135deg, #1e40af, #4f46e5);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.1rem;
		font-weight: 800;
		color: white;
		flex-shrink: 0;
	}

	.company-name {
		font-size: 0.95rem;
		font-weight: 700;
		color: #f1f5f9;
		margin: 0;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.job-title {
		font-size: 0.8rem;
		color: #64748b;
		margin: 3px 0 0 0;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.card-meta {
		display: flex;
		align-items: center;
		gap: 16px;
	}

	.meta-date,
	.meta-skills {
		font-size: 0.75rem;
		color: #475569;
	}

	.card-bottom {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding-top: 12px;
		border-top: 1px solid rgba(255, 255, 255, 0.05);
	}

	.details-btn {
		background: rgba(96, 165, 250, 0.1);
		border: 1px solid rgba(96, 165, 250, 0.2);
		border-radius: 8px;
		color: #60a5fa;
		padding: 6px 14px;
		font-size: 0.8rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s ease;
		display: flex;
		align-items: center;
		gap: 4px;
	}

	.details-btn:hover {
		background: rgba(96, 165, 250, 0.2);
		border-color: rgba(96, 165, 250, 0.4);
		transform: translateX(2px);
	}

	.details-btn span {
		transition: transform 0.2s ease;
	}

	.details-btn:hover span {
		transform: translateX(3px);
	}
</style>
