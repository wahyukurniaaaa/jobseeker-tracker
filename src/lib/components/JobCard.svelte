<script lang="ts">
	import type { JobApplication, ApplicationStatus } from '$lib/types';
	import { isPreferredLocation, getJobSource } from '$lib/types';
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

	const formatDate = (dateStr: string) =>
		new Date(dateStr).toLocaleDateString('id-ID', {
			day: 'numeric',
			month: 'short',
			year: 'numeric'
		});

	const preferred = $derived(isPreferredLocation(currentJob.location));
	const source = $derived(getJobSource(currentJob.job_url));
</script>

<article class="job-card">
	<header class="card-head">
		<div class="company-info">
			<div class="avatar">{currentJob.company_name.charAt(0).toUpperCase()}</div>
			<div class="head-text">
				<h3 class="title">{currentJob.job_title}</h3>
				<p class="company">{currentJob.company_name}</p>
			</div>
		</div>
		<MatchBadge score={currentJob.match_score} />
	</header>

	<div class="meta">
		<span class="source source-{source.toLowerCase()}">{source}</span>
		{#if currentJob.location}
			<span class="location" class:preferred>
				<svg viewBox="0 0 24 24" width="13" height="13" aria-hidden="true">
					<path
						fill="currentColor"
						d="M12 2a7 7 0 0 0-7 7c0 5.25 7 13 7 13s7-7.75 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"
					/>
				</svg>
				{currentJob.location}
			</span>
		{/if}
		<span class="date">{formatDate(currentJob.created_at)}</span>
	</div>

	{#if currentJob.job_description}
		<p class="description">{currentJob.job_description}</p>
	{/if}

	{#if currentJob.missing_skills && currentJob.missing_skills.length > 0}
		<div class="skills">
			{#each currentJob.missing_skills.slice(0, 3) as skill (skill)}
				<span class="skill">{skill}</span>
			{/each}
			{#if currentJob.missing_skills.length > 3}
				<span class="skill more">+{currentJob.missing_skills.length - 3}</span>
			{/if}
		</div>
	{/if}

	<footer class="card-foot">
		<StatusDropdown
			id={currentJob.id}
			bind:status={currentJob.status}
			onUpdate={handleStatusUpdate}
		/>
		<button class="details-btn" onclick={() => (showModal = true)}>Lihat detail</button>
	</footer>
</article>

{#if showModal}
	<DetailModal job={currentJob} onClose={() => (showModal = false)} />
{/if}

<style>
	.job-card {
		background: #161b27;
		border: 1px solid rgba(255, 255, 255, 0.07);
		border-radius: 14px;
		padding: 16px;
		display: flex;
		flex-direction: column;
		gap: 12px;
		transition:
			border-color 0.2s ease,
			background 0.2s ease;
	}

	.job-card:hover {
		border-color: rgba(255, 255, 255, 0.14);
		background: #181e2b;
	}

	.card-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 10px;
	}

	.company-info {
		display: flex;
		align-items: center;
		gap: 11px;
		min-width: 0;
	}

	.avatar {
		width: 40px;
		height: 40px;
		border-radius: 9px;
		background: #232a3a;
		border: 1px solid rgba(255, 255, 255, 0.08);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1rem;
		font-weight: 700;
		color: #cbd5e1;
		flex-shrink: 0;
	}

	.head-text {
		min-width: 0;
	}

	.title {
		font-size: 0.95rem;
		font-weight: 600;
		color: #f1f5f9;
		margin: 0;
		line-height: 1.3;
	}

	.company {
		font-size: 0.8rem;
		color: #94a3b8;
		margin: 2px 0 0;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.meta {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 6px 14px;
		font-size: 0.78rem;
		color: #64748b;
	}

	.source {
		display: inline-flex;
		align-items: center;
		padding: 1px 8px;
		border-radius: 5px;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.01em;
		background: rgba(255, 255, 255, 0.06);
		border: 1px solid rgba(255, 255, 255, 0.1);
		color: #cbd5e1;
	}

	.source-kalibrr {
		color: #f0abfc;
		border-color: rgba(240, 171, 252, 0.3);
		background: rgba(240, 171, 252, 0.08);
	}
	.source-glints {
		color: #fca5a5;
		border-color: rgba(252, 165, 165, 0.3);
		background: rgba(252, 165, 165, 0.08);
	}
	.source-jobstreet {
		color: #7dd3fc;
		border-color: rgba(125, 211, 252, 0.3);
		background: rgba(125, 211, 252, 0.08);
	}
	.source-linkedin {
		color: #93c5fd;
		border-color: rgba(147, 197, 253, 0.3);
		background: rgba(147, 197, 253, 0.08);
	}

	.location {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		color: #94a3b8;
	}

	.location.preferred {
		color: #34d399;
		font-weight: 500;
	}

	.location svg {
		flex-shrink: 0;
	}

	.description {
		font-size: 0.83rem;
		line-height: 1.55;
		color: #94a3b8;
		margin: 0;
		display: -webkit-box;
		-webkit-line-clamp: 3;
		line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.skills {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}

	.skill {
		font-size: 0.72rem;
		color: #94a3b8;
		background: rgba(255, 255, 255, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-radius: 6px;
		padding: 2px 8px;
	}

	.skill.more {
		color: #64748b;
	}

	.card-foot {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 10px;
		padding-top: 12px;
		border-top: 1px solid rgba(255, 255, 255, 0.06);
	}

	.details-btn {
		background: transparent;
		border: 1px solid rgba(255, 255, 255, 0.12);
		border-radius: 8px;
		color: #cbd5e1;
		padding: 7px 13px;
		font-size: 0.8rem;
		font-weight: 500;
		font-family: inherit;
		cursor: pointer;
		transition: all 0.15s ease;
		white-space: nowrap;
	}

	.details-btn:hover {
		background: rgba(255, 255, 255, 0.06);
		border-color: rgba(255, 255, 255, 0.2);
	}
</style>
