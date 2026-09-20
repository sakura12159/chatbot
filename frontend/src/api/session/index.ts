import {
    ChatSessionSchema,
    type ChatSession,
} from '@/api/session/schemas'
import { request } from '@/api/request';

export const createSession = (userId: string): Promise<ChatSession> => {
    return request(
        '/sessions',
        ChatSessionSchema,
        { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId })
        }
    )
}

export const getSession = (sessionId: string): Promise<ChatSession> => {
    return request(
        `/sessions/${sessionId}`,
        ChatSessionSchema,
        { method: 'GET' }
    )
}

export const deleteSession = (sessionId: string): Promise<void> => {
    return request(
        `/sessions/${sessionId}`,
        undefined,
        {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sessionId })
        }
    )
}
