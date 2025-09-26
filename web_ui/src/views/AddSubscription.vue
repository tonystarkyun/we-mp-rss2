<template>
  <div class="add-subscription">
    <a-page-header
      title="添加订阅"
      subtitle="添加新的公众号订阅"
      :show-back="true"
      @back="goBack"
    />
    
    <a-card>
      <a-form
        ref="formRef"
        :model="form"
        :rules="rules"
        layout="vertical"
        @submit="handleSubmit"
      >
        <a-form-item label="公众号名称" field="name">
          <a-space>
            <a-select
              v-model="form.name"
              placeholder="请输入公众号名称"
              allow-clear
              allow-search
              @search="handleSearch"
            >
            <a-option v-for="item of searchResults" :value="item.nickname" :label="item.nickname" @click="handleSelect(item)" />
          </a-select>
          </a-space>
        </a-form-item>
        
        <a-form-item label="头像" field="avatar">
          <a-avatar 
          :src=avatar_url
            v-model="form.avatar"
            placeholder="头像"
          >
          <img :src="avatar_url" width="80"/>
          </a-avatar>
        </a-form-item>
        <a-form-item label="公众号ID" field="accountId">
          <a-input
            readonly='readonly'
            v-model="form.wx_id"
            placeholder="请输入公众号ID"
          >
            <template #prefix><icon-idcard /></template>
          </a-input>
        </a-form-item>
        
        <a-form-item label="描述" field="description">
          <a-textarea
            v-model="form.description"
            placeholder="请输入公众号描述"
            :auto-size="{ minRows: 3, maxRows: 5 }"
            allow-clear
          />
        </a-form-item>
        
        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit" :loading="loading">
              添加订阅
            </a-button>
            <a-button @click="resetForm">重置</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { addSubscription,AddSubscriptionParams, searchBiz} from '@/api/subscription'
import {Avatar} from '@/utils/constants'
const router = useRouter()
const loading = ref(false)
const searchResults = ref([])
const avatar_url = ref('/static/default-avatar.png')
const formRef = ref(null)
const form = ref({
  name: '',
  wx_id: '',
  avatar:'',
  description: ''
})

// 监听 form.avatar 的变化
watch(() => form.value.avatar, (newValue, oldValue) => {
  console.log('头像地址已更新:', newValue);
  // 这里可以添加更多处理逻辑
  avatar_url.value=Avatar(newValue)
}, { deep: true });

const rules = {
  name: [
    { required: true, message: '请输入公众号名称' },
    { min: 2, max: 30, message: '公众号名称长度应在2-30个字符之间' }
  ],
  wx_id: [
    { required: true, message: '请输入公众号ID' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '公众号ID只能包含字母、数字、下划线和横线' }
  ],
  avatar: [
    { 
      required: true, 
      message: '请选择公众号头像',
      validator: (value: string) => {
        return value && value.startsWith('http')
      },
      message: '请选择有效的头像URL'
    }
  ],
  description: [
    { max: 200, message: '描述不能超过200个字符' }
  ]
}

const handleSearch = async (value: string) => {
  if (!value) {
    searchResults.value = []
    return
  }
  try {
    const res = await searchBiz(value, {
      kw: value,
      offset: 0,
      limit: 10
    })
    searchResults.value = res.list || []
  } catch (error) {
    console.error('搜索公众号失败:', error)
    searchResults.value = []
    
    // 检查是否是会话失效错误
    const errorMessage = error?.message || error?.detail?.message || error?.response?.data?.message || ''
    if (errorMessage.includes('invalid session') || 
        errorMessage.includes('代码:200003') || 
        errorMessage.includes('请重新扫码授权') ||
        errorMessage.includes('登录失效')) {
      Message.error({
        content: '微信公众号平台登录会话已失效，请重新扫码登录',
        duration: 5000
      })
      // 可以在这里添加跳转到登录页面或显示二维码的逻辑
      // router.push('/auth') // 如果有专门的认证页面
    } else {
      Message.error('搜索公众号失败，请稍后重试')
    }
  }
}

const handleSelect = (item: any) => {
  console.log(item)
  form.value.name = item.nickname
  form.value.wx_id = item.fakeid // 修正拼写错误：fackid → fakeid
  form.value.description = item.signature
  form.value.avatar = item.round_head_img
}

const handleSubmit = async () => {
  
  loading.value = true
  
  // 表单验证
  try {
    await formRef.value.validate()
  } catch (error) {
    Message.error(error?.errors?.join('\n') || '表单验证失败，请检查输入内容')
    loading.value = false
    return
  }

  // 表单提交
  try {
    await addSubscription({
      mp_name: form.value.name,
      mp_id: form.value.wx_id,
      avatar: form.value.avatar,
      mp_intro: form.value.description,
    })
    
    Message.success('订阅添加成功')
    router.push('/')
  } catch (error) {
    console.error('订阅添加失败:', error)
    Message.error(error.message || '订阅添加失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = {
    name: '',
    accountId: '',
    rssUrl: '',
    category: '',
    description: ''
  }
  searchResults.value = []
}

const goBack = () => {
  router.go(-1)
}
</script>

<style scoped>
.add-subscription {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.arco-form-item {
  margin-bottom: 20px;
}
</style>