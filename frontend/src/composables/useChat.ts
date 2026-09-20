import { reactive, ref, type Ref } from 'vue';
import {
    type SSEChunkData,
    type AIMessageContent,
    type ChatStatus,
    useChat as useChatT,
    type ChatStreamPayload,
    type ChatRequestParams,
    type ChatMessagesData
} from '@tdesign-vue-next/chat'
import { BASE_URL } from '@/api/request';
import { ChatResponseChunkSchema } from '@/api/chat/schemas';
import { useSession } from '@/composables/useSession';
import { useSender } from '@/composables/useSender';

type chatInstanceType = {
    messages: Ref<ChatMessagesData[]>
    status: Ref<ChatStatus>,
    chat: (query: string) => Promise<void>,
    regenerateChat: () => Promise<void>,
    abortChat: () => void,
    setMessages: (messages?: ChatMessagesData[]) => void,
    resetChatInstance: () => void
}

let chatInstance: chatInstanceType | null = null;

export const useChat = (): chatInstanceType => {
    if (chatInstance !== null) return chatInstance;
    return createChatInstance();
}

export const createChatInstance = (): chatInstanceType => {
    
    const session = useSession();
    const sender = useSender();

    const lastQuery = ref<string>();
    const regenerate = ref<boolean>(false);
    const chatRequestParams = reactive({
        sessionId: session.sessionId,
        thinking: sender.thinking,
        web: sender.web,
        regenerate: regenerate
    })
    
    const chatIsAborted = ref<boolean>(false);

    const { chatEngine, messages, status } = useChatT({
        defaultMessages: undefined,
        chatServiceConfig: {
            // 对话服务地址
            endpoint: `${BASE_URL}/chat`,
            // 开启流式传输
            transport: 'sse',
            // 请求数据
            onRequest: (params: ChatRequestParams): RequestInit => {
                const { prompt, ...rest } = params;
                return {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'text/event-stream'
                    },
                    body: JSON.stringify({
                        query: prompt,
                        ...rest
                    })
                };
            },
            // 收到消息
            onMessage: (chunk: SSEChunkData<ChatStreamPayload>): AIMessageContent | null => {
                // 使用 zod 检验收窄类型
                const result = ChatResponseChunkSchema.safeParse(chunk.data);
                if (!result.success) return null;
                
                const { type, content, reasoningContent, reasoningTime } = result.data;
                switch (type) {
                    case 'text':
                        return {
                            type: 'text',
                            data: content ?? '',
                        };
                    case 'markdown':
                        return {
                            type: 'markdown',
                            data: content ?? '',
                        }
                    case 'thinking':
                        return {
                            type: 'thinking',
                            status: reasoningTime ? 'complete' : 'streaming',
                            data: {
                                title: reasoningTime ? `思考完成（耗时${reasoningTime.toFixed(1)}秒）` : '思考中...',
                                text: reasoningContent ?? ''
                            }
                        };
                }
                return null;
            },
            onStart: () => {
                // console.log('传输开始')
            },
            // 传输完成或中断
            onComplete: (isAborted: boolean): void => {
                // console.log('传输完成')
                chatIsAborted.value = isAborted;
            },
            // 流式块校验
            isValidChunk: (chunk: SSEChunkData): boolean => {
                // 使用 zod 检验收窄类型
                return ChatResponseChunkSchema.safeParse(chunk.data).success;
            },
        }
    });

    const findLastQuery = (): void => {
        for (let i = messages.value.length - 1; i >= 0; i--) {
            if (messages.value.at(i)?.role === 'user') {
                lastQuery.value = messages.value.at(i)?.content?.at(0)?.data as string;
                console.log(lastQuery.value)
                break
            }
        }
    }

    const setMessages = (messages?: ChatMessagesData[]): void => {
        if (messages === undefined) {
            chatEngine.value?.clearMessages();
        } else {
            chatEngine.value?.setMessages(messages);
        }
    }

    const chat = async (query: string): Promise<void> => {
        lastQuery.value = query;
        chatIsAborted.value = false;
        await chatEngine.value?.sendUserMessage({ prompt: query, ...chatRequestParams });
    }

    const regenerateChat = async (): Promise<void> => {
        findLastQuery();
        if (lastQuery.value === undefined) {
            throw new Error('No previous input, should query first.');
        }

        setMessages(messages.value.slice(0, -2));

        if (!chatIsAborted.value) {
            regenerate.value = true;
        }
        await chat(lastQuery.value);
        regenerate.value = false;
    }

    const abortChat = (): void => {
        chatIsAborted.value = true;
        chatEngine.value?.abortChat();
    }
    
    const resetChatInstance = (): void => { 
        chatEngine.value?.abortChat();
        chatInstance = null;
     };

     chatInstance = {
        messages,
        status,
        chat,
        regenerateChat,
        abortChat,
        setMessages,
        resetChatInstance
    };

    return chatInstance;
}
