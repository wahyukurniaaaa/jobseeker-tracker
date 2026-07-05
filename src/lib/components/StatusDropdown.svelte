<script lang="ts">
	import type { ApplicationStatus } from '$lib/types';
	import { supabase } from '$lib/supabaseClient';

	interface Props {
		id: string;
		status: ApplicationStatus;
		onUpdate?: (id: string, newStatus: ApplicationStatus) => void;
	}

	let { id, status = $bindable(), onUpdate }: Props = $props();

	const statuses: ApplicationStatus[] = ['To Apply', 'Applied', 'Interview', 'Rejected'];

	let isUpdating = $state(false);
	let error = $state<string | null>(null);

	const statusConfig: Record<ApplicationStatus, { color: string; icon: string }> = {
		'To Apply': { color: 'status-toapply', icon: '📋' },
		Applied: { color: 'status-applied', icon: '📨' },
		Interview: { color: 'status-interview', icon: '🎯' },
		Rejected: { color: 'status-rejected', icon: '❌' }
	};

	async function handleChange(event: Event) {
		const select = event.target as HTMLSelectElement;
		const newStatus = select.value as ApplicationStatus;
		if (newStatus === status) return;

		isUpdating = true;
		error = null;

		const { error: err } = await supabase
			.from('job_applications')
			.update({ status: newStatus })
			.eq('id', id);

		if (err) {
			error = 'Gagal update status';
			select.value = status;
		} else {
			status = newStatus;
			onUpdate?.(id, newStatus);
		}
		isUpdating = false;
	}
</script>

<div class="status-wrapper">
	<select
		class="status-select {statusConfig[status].color}"
		value={status}
		onchange={handleChange}
		disabled={isUpdating}
	>
		{#each statuses as s}
			<option value={s}>{statusConfig[s].icon} {s}</option>
		{/each}
	</select>
	{#if isUpdating}
		<span class="spinner"></span>
	{/if}
	{#if error}
		<span class="error-msg">{error}</span>
	{/if}
</div>

<style>
	.status-wrapper {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.status-select {
		border: 1px solid;
		border-radius: 8px;
		padding: 5px 10px;
		font-size: 0.8rem;
		font-weight: 600;
		cursor: pointer;
		outline: none;
		transition: all 0.2s ease;
		background: transparent;
		appearance: none;
		-webkit-appearance: none;
		padding-right: 28px;
		background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23888' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
		background-repeat: no-repeat;
		background-position: right 8px center;
	}
	.status-select:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.status-toapply {
		color: #94a3b8;
		border-color: rgba(148, 163, 184, 0.4);
		background-color: rgba(148, 163, 184, 0.08);
	}
	.status-applied {
		color: #60a5fa;
		border-color: rgba(96, 165, 250, 0.4);
		background-color: rgba(96, 165, 250, 0.08);
	}
	.status-interview {
		color: #a78bfa;
		border-color: rgba(167, 139, 250, 0.4);
		background-color: rgba(167, 139, 250, 0.08);
	}
	.status-rejected {
		color: #f87171;
		border-color: rgba(248, 113, 113, 0.4);
		background-color: rgba(248, 113, 113, 0.08);
	}
	.spinner {
		width: 14px;
		height: 14px;
		border: 2px solid rgba(255, 255, 255, 0.2);
		border-top-color: #60a5fa;
		border-radius: 50%;
		animation: spin 0.6s linear infinite;
		flex-shrink: 0;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
	.error-msg {
		font-size: 0.7rem;
		color: #f87171;
	}
</style>
