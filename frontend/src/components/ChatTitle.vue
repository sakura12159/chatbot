<template>
    <h3 v-if="session.sessionId.value !== undefined">{{ session.title }} - {{ session.tokenUsage }} tokens</h3>
</template>

<script setup lang="ts">
    import { useSession } from '@/composables/useSession';

    const session = useSession();
</script>

<style></style>
