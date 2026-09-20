<template>
    <t-space align="center" size="small">
        <t-button
            variant="outline"
            shape="round"
            :theme="sender.thinking.value ? 'primary' : 'default'"
            @click="sender.thinking.value = !sender.thinking.value"
        >
            <template #icon>
                <t-icon name="lightbulb" />
            </template>
            深度思考
        </t-button>
        <t-button
            variant="outline"
            :theme="sender.web.value ? 'primary' : 'default'"
            shape="round"
            @click="sender.web.value = !sender.web.value"
        >
            <template #icon>
                <t-icon name="internet" />
            </template>
            联网查询
        </t-button>
    </t-space>
</template>

<script setup lang="ts">
    import { useSender } from '@/composables/useSender';
    
    const sender = useSender();
</script>

<style scoped>
</style>