import { 
    UserSchema, 
    BalanceInfoSchema, 
    type User, 
    type BalanceInfo
} from '@/api/user/schemas';
import {
    ChatSessionInfoListSchema, 
    type ChatSessionInfoList
} from '@/api/session/schemas';
import { request } from '@/api/request';

export const signIn = (name: string): Promise<User> => {
    return request(
        '/users',
        UserSchema,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        }
    )
}

export const deregister = (userId: string): Promise<void> => {
    return request(
        `/users/${userId}`,
        undefined,
        { 
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId })
        }
    )
}

export const listSessions = (userId: string): Promise<ChatSessionInfoList> => {
    return request(
        `/users/${userId}/sessions`,
        ChatSessionInfoListSchema,
        { method: 'GET' }
    )
}

export const inquireBalance = (userId: string): Promise<BalanceInfo> => {
    return request(
        `/users/${userId}/balance`,
        BalanceInfoSchema,
        { method: 'GET' }
    )
}
