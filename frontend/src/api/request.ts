import { z } from 'zod'

export const BASE_URL = 'http://127.0.0.1:8000/api/v1';

export function request<T>(
    url: string,
    schema: z.ZodType<T>,
    options?: RequestInit
): Promise<T>

export function request(
    url: string,
    schema: undefined,
    options?: RequestInit
): Promise<void>

export async function request<T>(
    url: string,
    schema?: z.ZodType<T>,
    options?: RequestInit
): Promise<T | void> {
    const res = await fetch(`${BASE_URL}${url}`, options);

    // 请求失败抛出异常
    if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }

    // 无返回值类型校验
    if (schema === undefined) {
        return
    }

    // 先读文本，再 parse，避免空 body 抛错
    const text = await res.text();
    const json = text ? JSON.parse(text) : null;

    // 用 safeParse 校验
    const result = schema.safeParse(json);
    if (!result.success) {
        console.error('API 响应格式错误:', z.treeifyError(result.error));
        throw new Error('API_TYPE_NOT_MATCH');
    }
    return result.data;
}
