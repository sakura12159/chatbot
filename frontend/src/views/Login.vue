<template>
    <div class="login">
    <t-form 
        ref="form" 
        :data="formData" 
        :rules="rules"
        :label-width="0" 
        @reset="handleReset" 
        @submit="handleSubmit"
    >
        <t-form-item name="username">
            <t-input class="login__username" v-model="formData.userName" clearable placeholder="请输入用户名，不存在时自动注册">
                <template #prefix-icon>
                    <desktop-icon />
                </template>
            </t-input>
        </t-form-item>

        <t-form-item>
            <t-button theme="primary" type="submit" block>登录</t-button>
        </t-form-item>
    </t-form>
    </div>
</template>

<script setup lang="ts">
    import { ref } from 'vue';
    import { useRouter } from 'vue-router';
    import { type FormProps } from 'tdesign-vue-next'
    import { signIn } from '@/api/user';
    import { useUser } from '@/composables/useUser';
    import { useStatusStore } from '@/stores/useStatusStore';

    const router = useRouter();
    const user = useUser();
    const statusStore = useStatusStore();

    const formData = ref<{ userName: string }>({ userName: '' });
    const rules: FormProps['rules'] = {
        userName: [
            {
                required: true,
                message: '必填'
            }
        ]
    }

    const handleReset: FormProps['onReset'] = () => {
        console.log('登录信息重置');
    };
    const handleSubmit: FormProps['onSubmit'] = async ({ validateResult, firstError }) => {
        console.log('登录信息提交');
        if (validateResult === true) {        
            user.userName.value = formData.value.userName;
            user.userId.value = (await signIn(formData.value.userName)).id;
            statusStore.isLoggedIn = true;

            await router.push('/chat');
        } else {
            console.log('登录信息验证失败：', firstError, validateResult);
        }
    };
</script>

<style scoped>
.login {
    height: 100dvh;

    display: flex;
    justify-content: center; /* 水平居中 */
    align-items: center;     /* 垂直居中 */
}

.login__username, .login__apiKey {
    width: 500px;
}
</style>