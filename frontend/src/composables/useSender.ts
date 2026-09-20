import { ref } from 'vue';

const input = ref<string>('');
const thinking = ref<boolean>(false);
const web = ref<boolean>(false);

export const useSender = () => {
    const resetInput = (): void => {
        input.value = '';
    }

    const resetThinking = (): void => {
        thinking.value = false;
    }

    const resetWeb = (): void => {
        web.value = false;
    }

    const reset = (): void => {
        resetInput();
        resetThinking();
        resetWeb();
    }

    return {
        input,
        thinking,
        web,
        resetInput,
        resetThinking,
        resetWeb,
        reset
    }
}
