<template>
    <t-layout class="chat__options">
        <t-layout class="chat__operations">
            <t-content>
                <t-menu>
                    <t-menu-item value="createSession" :onClick="handleCreateSession">
                        <template #icon>
                            <t-icon name="add" />
                        </template>
                        新建会话
                    </t-menu-item>
                </t-menu>
            </t-content>
        </t-layout>
        <t-layout class="chat__session-list">
            <t-header class="chat__session-header">最近</t-header>
            <t-content class="chat__sessions">
                <t-menu expandType="popup">
                    <t-submenu 
                        class="chat__session" 
                        v-for="{ id, title } in session.sessionList.value?.sessions" 
                        :key="id" 
                        :value="title" 
                        :title="title"
                    >
                        <t-menu-item :value="`loadSession-${id}`" :onClick="async () => handleLoadSession(id)">
                            加载会话
                        </t-menu-item>
                        <t-menu-item :value="`deleteSession-${id}`" :onClick="async () => handleDeleteSession(id)">
                            <span style="color: red;">删除会话</span>
                        </t-menu-item>
                    </t-submenu>
                </t-menu>
            </t-content>
        </t-layout>
    </t-layout>
</template>

<script lang="ts" setup>
    import type { AIMessage, ChatMessagesData, MarkdownContent, ThinkingContent, UserMessage } from '@tdesign-vue-next/chat';
    import { onMounted, watch } from 'vue';
    import { useUser } from '@/composables/useUser';
    import { useSession } from '@/composables/useSession';
    import { useChat } from '@/composables/useChat';
    import { 
        createSession, 
        getSession,
        deleteSession 
    } from '@/api/session/index';
    import { type ChatMessage } from '@/api/message/schemas';
    
    const user = useUser();
    const session = useSession();
    const chat = useChat();

    const formatMessages = (messages: ChatMessage[]): ChatMessagesData[] => {
        const ret = [];
        let prevIsThinking: boolean = false;  // 是否需要拼接推理内容、补上模型回答或设置推理部分标题
        let prevThinkingAIMessage: AIMessage | null = null;  // 前一条推理信息的指针
        for (const { id, type, role, content, reasoningContent, reasoningTime, createdAt } of messages) {
            switch (role) {
                case 'system': 
                    break
                case 'tool': 
                    break
                case 'assistant':
                    switch (type) {
                        case 'markdown':
                            ret.push({
                                id,
                                role,
                                content: [{ type, data: content, status: 'complete' }], 
                                datetime: new Date(createdAt).toISOString()
                            } as AIMessage)
                            break
                        case 'thinking':
                            if (prevIsThinking) {
                                (prevThinkingAIMessage?.content?.at(0) as ThinkingContent).data.text += reasoningContent ?? '';  // 拼接推理内容
                                (prevThinkingAIMessage?.content?.at(1) as MarkdownContent).data = content;  // 设置模型回答
                                if (reasoningTime !== null) (prevThinkingAIMessage?.content?.at(0) as ThinkingContent).data.title = `思考完成（耗时${reasoningTime.toFixed(1)}秒）`;  // 设置标题
                            } else {
                                ret.push({
                                    id,
                                    role,
                                    content: [
                                        { type, data: { title: reasoningTime ? `思考完成（耗时${reasoningTime.toFixed(1)}秒）` : undefined, text: reasoningContent ?? '' }, status: 'complete' },
                                        { type: 'markdown', data: content, status: 'complete' }
                                    ], 
                                    datetime: new Date(createdAt).toISOString()
                                } as AIMessage);
                                prevThinkingAIMessage = ret.at(-1) as AIMessage;
                            }
                            break
                    }
                    break
                case 'user':
                    ret.push({
                        id,
                        role,
                        content: [{ type, data: content, status: 'complete' }],
                        datetime: new Date(createdAt).getTime().toString()
                    } as UserMessage)
                    break
            }
            prevIsThinking = type === 'thinking' || type === 'tool_call';
        }
        return ret;
    }

    const handleCreateSession = async (): Promise<void> => {
        console.log('创建会话');
        const newSession = await createSession(user.userId.value!);
        session.sessionId.value = newSession.id;
        session.title.value = newSession.title;
        session.tokenUsage.value = newSession.totalTokens;
        chat.setMessages();
        await handleListSessions();
    }

    const handleListSessions = async (): Promise<void> => {
        console.log('获取会话列表');
        await session.loadSessionList(user.userId.value!);
        
        if (session.sessionId.value !== undefined) {
            const currentSession = await getSession(session.sessionId.value);
            session.title.value = currentSession.title;
            session.tokenUsage.value = currentSession.totalTokens;
        }
    }

    const handleLoadSession = async (sessionId: string): Promise<void> => {
        console.log('加载会话');
        const currentSession = await getSession(sessionId);
        chat.setMessages(formatMessages(currentSession.messages));
        session.sessionId.value = sessionId;
        session.title.value = currentSession.title;
        session.tokenUsage.value = currentSession.totalTokens;
    }
    
    const handleDeleteSession = async (sessionId: string): Promise<void> => {
        console.log('删除会话');
        if (sessionId == session.sessionId.value) {
            session.resetSessionId();
            session.resetTitle();
            session.resetTokenUsage();
            chat.setMessages();
        }
        await deleteSession(sessionId);
        await handleListSessions();
    }

    watch(
        chat.status, 
        async (value) => {
            if (value === 'complete') await handleListSessions();
        }
    )

    onMounted(handleListSessions)
</script>

<style scoped>
.chat__options {
    display: flex;
    flex-direction: column;

    min-height: 0;

    background-color: white;

    border-right: 0.5px dashed;
}

.chat__operations {
    flex: 0 0 300px;
}

.chat__session-list {
    flex: 1;

    min-height: 0;

    background-color: white;
}

.chat__session-header {
    padding-left: 20px; 

    font-size: medium; 
    font-weight: bold;
}

.chat__sessions {
    min-height: 0;

    overflow: auto;

    background-color: white;
}

.chat__session {
    padding-right: 10px;
}
</style>