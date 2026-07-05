<script lang="ts">
	interface Props {
		score: number;
	}

	let { score }: Props = $props();

	const level = $derived(score >= 80 ? 'high' : score >= 50 ? 'medium' : 'low');
</script>

<span class="match-badge {level}">
	<span class="dot"></span>
	<strong>{score}</strong>
	<span class="unit">match</span>
</span>

<style>
	.match-badge {
		display: inline-flex;
		align-items: baseline;
		gap: 5px;
		padding: 3px 9px;
		border-radius: 7px;
		font-size: 0.75rem;
		font-weight: 500;
		white-space: nowrap;
		background: rgba(255, 255, 255, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.08);
		color: #cbd5e1;
	}

	.match-badge strong {
		font-weight: 700;
		font-size: 0.82rem;
	}

	.unit {
		color: #64748b;
		font-size: 0.68rem;
	}

	.dot {
		align-self: center;
		width: 7px;
		height: 7px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.high .dot {
		background: #22c55e;
	}
	.medium .dot {
		background: #eab308;
	}
	.low .dot {
		background: #ef4444;
	}
</style>
