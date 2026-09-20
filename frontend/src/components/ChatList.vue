<template>
    <t-chat-list :clear-history="false">
        <t-chat-message
            v-for="(message, idx) in chat.messages.value"
            :key="message.id"
            :message="message"
            :variant="'outline'"
            :placement="message.role === 'user' ? 'right' : 'left'"
            :avatar="message.role === 'user' ? 'https://tdesign.gtimg.com/site/avatar.jpg' : 'https://tdesign.gtimg.com/site/chat-avatar.png'"
            :chat-content-props="
            message.role === 'assistant'
                ? {
                    thinking: {
                    maxHeight: 150,
                    layout: 'block',
                    collapsed: message.content?.find((item) => item.type === 'thinking')?.status === 'complete',
                    },
                }
                : {}
            "
            allow-content-segment-custom
        >
            <t-chat-actionbar
                v-if="isAIMessage(message)"
                slot="actionbar"
                :content="message.content?.map(content => content.data).join('')"
                :action-bar="getActionBar(message, idx === chat.messages.value.length - 1)"
                :copy-text="getMessageContentForCopy(message)"
                @actions="handleAction"
            />
            <t-chat-loading v-else animation="dot" />
            <template #name>{{ message.role.at(0)?.toUpperCase() + message.role.slice(1) }}</template>
            <template v-if="message.role === 'assistant'" #datetime> {{ new Date(message.datetime as string).toLocaleString() }}</template>
            <template v-else #datetime> {{ new Date(Number(message.datetime as string)).toLocaleString() }}</template>
        </t-chat-message>
    </t-chat-list>
</template>

<script setup lang="ts">
    import { 
        type ChatMessagesData,
        type TdChatActionsName,isAIMessage, 
        getMessageContentForCopy
    } from '@tdesign-vue-next/chat';
    import { useChat } from '@/composables/useChat';

    const chat = useChat();
    
    // 操作按钮配置
    const getActionBar = (message: ChatMessagesData, isLast: boolean): TdChatActionsName[] => {
        const actions: TdChatActionsName[] = ['copy', 'good', 'bad'];
        if (isLast) {
            actions.push('replay');
        }
        return actions;
    };

    // 底部操作栏处理
    const handleAction = (name: string, data?: any) => {
        console.log('触发操作栏action', name, 'data', data);
        switch (name) {
            case 'copy':
                console.log('复制');
                break;
            case 'good':
                console.log('点赞', data);
                break;
            case 'bad':
                console.log('点踩', data);
                break;
            case 'replay':
                console.log('重新生成');
                chat.regenerateChat();
                break;
            default:
                console.log('其他操作', name, data);
        }
    };
</script>

<style scoped>
</style>