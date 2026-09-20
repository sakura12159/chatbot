<template>
    <t-chat-sender
        v-model="sender.input.value"
        :textarea-props="{
            placeholder: '有问题，尽管问～ Enter 发送，Shift+Enter 换行',
        }"
        :disabled="chat.status.value === 'pending' || chat.status.value === 'streaming'"
        :loading="chat.status.value === 'pending' || chat.status.value === 'streaming'"
        @send="handleSend"
        @stop="handleAbort"
    >
        <!-- 自定义输入框底部区域 -->
        <template #footer-prefix>
            <ChatSenderButtons />
        </template>
    </t-chat-sender>
</template>

<script setup lang="ts">
    import ChatSenderButtons from '@/components/ChatSenderButtons.vue';
    import { useSender } from '@/composables/useSender';
    import { useUser } from '@/composables/useUser';
    import { useSession } from '@/composables/useSession';
    import { useChat } from '@/composables/useChat';
    import { createSession } from '@/api/session';

    const sender = useSender();
    const user = useUser();
    const session = useSession();
    const chat = useChat();
    
    // 发送消息
    const handleSend = async (value: string) => {
        console.log('发送聊天内容');
        if (session.sessionId.value === undefined) {
            session.sessionId.value = (await createSession(user.userId.value!)).id;
        }
        await chat.chat(value);
        sender.resetInput();
    };

    // 停止生成
    const handleAbort = () => {
        console.log('停止生成');
        chat.abortChat();
    };
</script>

<style scoped>
</style>