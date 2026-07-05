<script lang="ts">
	interface Props {
		score: number;
	}

	let { score }: Props = $props();

	const getBadgeClass = (score: number) => {
		if (score >= 80) return 'badge-green';
		if (score >= 50) return 'badge-yellow';
		return 'badge-red';
	};

	const getLabel = (score: number) => {
		if (score >= 80) return '🟢 High';
		if (score >= 50) return '🟡 Medium';
		return '🔴 Low';
	};
</script>

<span class="match-badge {getBadgeClass(score)}">
	{getLabel(score)}
	<strong>{score}%</strong>
</span>

<style>
	.match-badge {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		padding: 3px 10px;
		border-radius: 999px;
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.02em;
		white-space: nowrap;
	}
	.badge-green {
		background: rgba(34, 197, 94, 0.15);
		color: #22c55e;
		border: 1px solid rgba(34, 197, 94, 0.3);
	}
	.badge-yellow {
		background: rgba(234, 179, 8, 0.15);
		color: #eab308;
		border: 1px solid rgba(234, 179, 8, 0.3);
	}
	.badge-red {
		background: rgba(239, 68, 68, 0.15);
		color: #ef4444;
		border: 1px solid rgba(239, 68, 68, 0.3);
	}
</style>
