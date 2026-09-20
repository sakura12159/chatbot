<template>
    <t-layout class="chat">
        <t-header class="chat__header">
            <t-head-menu value="menu">
                <template #logo>
                    <p style="font-weight: bolder; font-size: larger;">A Chatbot</p>
                </template>
                <template #operations>
                    <span style="margin-right: 20px;">你好，{{ user.userName }}！{{ user.balanceMessage }}</span>
                    <t-space style="padding-right: 50px;">
                        <t-button @click="handleSignOut">
                            <template #icon>
                                <t-icon name="user-arrow-right" />
                                登出
                            </template>
                        </t-button>
                        <t-button @click="handleDeregisterUser" theme="danger">
                            <template #icon>
                                <t-icon name="user-clear" />
                                注销
                            </template>
                        </t-button>
                    </t-space>
                </template>
            </t-head-menu>
        </t-header>
        <t-layout class="chat__body">
            <t-aside class="chat__sidebar">
                <ChatSidebar />
            </t-aside>
            <t-layout class="chat__main">
                <t-header class="chat__title">
                    <ChatTitle id="chat-title"/>
                </t-header>
                <t-content class="chat__list">
                    <ChatList id="chat-list"/>
                </t-content>
                <t-footer class="chat__sender">
                    <ChatSender id="chat-sender"/>
                </t-footer>
            </t-layout>
        </t-layout>
        <!-- <t-footer class="chat__footer"></t-footer> -->
    </t-layout>
</template>

<script setup lang="ts">
    import { onMounted, onUnmounted } from 'vue';
    import router from '@/routers';
    import { inquireBalance, deregister } from '@/api/user';
    import { useUser } from '@/composables/useUser';
    import { useSession } from '@/composables/useSession';
    import { useChat } from '@/composables/useChat';
    import { useSender } from '@/composables/useSender';
    import { useStatusStore } from '@/stores/useStatusStore';
    import ChatTitle from '@/components/ChatTitle.vue';
    import ChatList from '@/components/ChatList.vue';
    import ChatSender from '@/components/ChatSender.vue';
    import ChatSidebar from '@/components/ChatSidebar.vue';
    
    const user = useUser();
    const session = useSession();
    const sender = useSender();
    const chat = useChat();
    const statusStore = useStatusStore();

    const handleSignOut = async () => {
        console.log('用户登出');
        user.reset();
        session.reset();
        statusStore.reset();
        chat.resetChatInstance();
        sender.reset();

        await router.push('/login');
    }

    const handleDeregisterUser = async () => {
        console.log('注销用户');
        await deregister(user.userId.value!);
        user.reset();
        session.reset();
        statusStore.reset();
        chat.resetChatInstance();
        sender.reset();

        await router.push('/login');
    }

    const handleInquireBalance = async () => {
        console.log('查询用户余额');
        const balanceInfo = await inquireBalance(user.userId.value!);
        user.balanceMessage.value = 
        balanceInfo.isAvailable ?
        `账户剩余 ${balanceInfo.totalBalance} ${balanceInfo.currency}` :
        '账户不可用'                
    }

    let timer: number | undefined = undefined;
    onMounted(() => {
        if (user.userId.value === undefined) throw new Error('UserId is undefined.');
        if (user.userName.value === undefined) throw new Error('UserName is undefined.');
        
        handleInquireBalance();
        timer = setInterval(handleInquireBalance, 5 * 60 * 1000);
    })

    onUnmounted(() => {
        clearInterval(timer);
    })
</script>

<style scoped>
.chat {
    display: flex;
    flex-direction: column;

    height: 100dvh;
}

.chat__body {
    flex: 1;

    min-height: 0;

    background-color: white;
}

.chat__sidebar {
    display: flex;

    min-height: 0;

    margin: 0px 10px;
}

.chat__main {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;

    overflow-x: hidden;
    
    padding: 20px 50px;

    background-color: white;
}

.chat__title {
    background-color: white;
}

.chat__list {
    flex: 1;
    min-height: 0;
    overflow: hidden;

    padding: 0px 200px;
}

.chat__sender {
    margin: 20px 0px;
    padding: 0px 100px;
}

.chat__footer {
    background-color: white;
}

#chat-list {
    height: 100%;
}
</style>
