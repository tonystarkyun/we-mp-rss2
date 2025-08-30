<template>
  <div class="add-industry">
    <a-page-header
      title="添加行业动态"
      subtitle="添加新的行业动态链接"
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
        <a-form-item label="行业网站链接" field="url">
          <a-input
            v-model="form.url"
            placeholder="请输入行业网站URL，例如：https://www.industry.com"
            allow-clear
          >
            <template #prefix><icon-link /></template>
          </a-input>
          <template #help>
            <div style="color: #666; margin-top: 4px;">
              系统将自动爬取该行业网站的文章列表
            </div>
          </template>
        </a-form-item>

        <a-form-item label="名称" field="name">
          <a-input
            v-model="form.name"
            placeholder="行业网站名称（留空将自动提取）"
            allow-clear
          >
            <template #prefix><icon-tag /></template>
          </a-input>
        </a-form-item>
        
        <a-form-item label="描述" field="description">
          <a-textarea
            v-model="form.description"
            placeholder="行业网站描述（留空将自动提取）"
            :auto-size="{ minRows: 2, maxRows: 4 }"
            allow-clear
          />
        </a-form-item>

        <!-- 爬虫测试区域 -->
        <a-form-item label="爬虫测试" v-if="form.url">
          <a-space direction="vertical" style="width: 100%;">
            <a-button @click="testCrawl" :loading="testLoading" type="outline">
              <template #icon><icon-bug /></template>
              测试爬取该行业网站
            </a-button>
            
            <div v-if="testResult && !testLoading" class="test-result">
              <a-alert
                :type="testResult.success ? 'success' : 'error'"
                :title="testResult.success ? '爬取成功' : '爬取失败'"
                :description="testResult.message"
                show-icon
              />
              
              <div v-if="testResult.success && testResult.data" style="margin-top: 12px;">
                <a-descriptions :column="1" bordered size="small">
                  <a-descriptions-item label="网站标题">
                    {{ testResult.data.website_info?.title || '未获取到' }}
                  </a-descriptions-item>
                  <a-descriptions-item label="网站描述">
                    {{ testResult.data.website_info?.description || '未获取到' }}
                  </a-descriptions-item>
                  <a-descriptions-item label="找到文章数">
                    {{ testResult.data.articles_found || 0 }} 篇
                  </a-descriptions-item>
                </a-descriptions>

                <div v-if="testResult.data.articles && testResult.data.articles.length > 0" style="margin-top: 12px;">
                  <h4>文章预览（前3篇）：</h4>
                  <a-list :data="testResult.data.articles.slice(0, 3)" size="small">
                    <template #item="{ item }">
                      <a-list-item>
                        <a-list-item-meta>
                          <template #title>
                            <a :href="item.url" target="_blank" style="color: #1677ff;">
                              {{ item.title }}
                            </a>
                          </template>
                          <template #description>
                            提取时间: {{ item.extracted_at }}
                          </template>
                        </a-list-item-meta>
                      </a-list-item>
                    </template>
                  </a-list>
                </div>
              </div>
            </div>
          </a-space>
        </a-form-item>
        
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="handleSubmit" :loading="loading">
              <template #icon><icon-plus /></template>
              添加行业
            </a-button>
            <a-button @click="resetForm">重置</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { addIndustry, testIndustryCrawl } from '@/api/industry'

const router = useRouter()
const loading = ref(false)
const testLoading = ref(false)
const testResult = ref(null)

const formRef = ref(null)
const form = ref({
  url: '',
  name: '',
  description: ''
})

const rules = {
  url: [
    { required: true, message: '请输入行业网站URL' },
    {
      validator: (value, callback) => {
        if (value && !value.match(/^https?:\/\/.+/)) {
          callback('请输入有效的URL（以http://或https://开头）')
        } else {
          callback()
        }
      }
    }
  ]
}

const goBack = () => {
  router.go(-1)
}

const resetForm = () => {
  form.value = {
    url: '',
    name: '',
    description: ''
  }
  testResult.value = null
}

const testCrawl = async () => {
  if (!form.value.url) {
    Message.warning('请先输入行业网站URL')
    return
  }

  testLoading.value = true
  testResult.value = null

  try {
    const response = await testIndustryCrawl(form.value.url, 5)
    
    // 添加调试信息
    console.log('API响应:', response)
    console.log('响应结构:', JSON.stringify(response, null, 2))
    
    // 检查响应是否成功
    if (response.code === 0 || response.data?.code === 0 || response.crawl_success === true) {
      const data = response.data || response
      testResult.value = {
        success: true,
        message: `成功爬取到 ${data.articles_found} 篇文章`,
        data: data
      }
      
      // 自动填充表单
      if (!form.value.name && data.website_info?.title) {
        form.value.name = data.website_info.title
      }
      if (!form.value.description && data.website_info?.description) {
        form.value.description = data.website_info.description
      }
      
      Message.success('爬取测试成功！已自动填充行业网站信息')
    } else {
      testResult.value = {
        success: false,
        message: response.data?.error || response.error || '爬取失败'
      }
    }
  } catch (error) {
    testResult.value = {
      success: false,
      message: error.message || '网络请求失败'
    }
    Message.error('爬取测试失败')
  } finally {
    testLoading.value = false
  }
}

const handleSubmit = async (e) => {
  console.log('表单提交被触发', e)
  try {
    console.log('开始表单验证...')
    console.log('formRef.value:', formRef.value)
    
    // 检查表单引用是否存在
    if (!formRef.value) {
      console.error('表单引用不存在')
      Message.error('表单初始化失败')
      return
    }
    
    const validationResult = await formRef.value.validate()
    console.log('表单验证结果:', validationResult)
    
    // 手动验证
    if (!form.value.url) {
      Message.error('请输入行业网站URL')
      return
    }
    
    if (!form.value.url.match(/^https?:\/\/.+/)) {
      Message.error('请输入有效的URL（以http://或https://开头）')
      return
    }
    
    loading.value = true
    console.log('准备发送添加行业请求:', {
      url: form.value.url,
      name: form.value.name,
      avatar: '',
      description: form.value.description
    })
    
    const response = await addIndustry({
      url: form.value.url,
      name: form.value.name,
      avatar: '', // 使用默认头像
      description: form.value.description
    })
    
    console.log('添加行业API响应:', response)
    
    if (response.code === 0 || response.data?.code === 0 || response.message === '行业动态链接添加成功') {
      Message.success('行业动态链接添加成功！')
      router.push('/industries')
    } else {
      Message.error(response.message || response.data?.message || '添加行业动态链接失败')
    }
  } catch (error) {
    console.error('添加行业错误:', error)
    Message.error(error.message || '添加行业动态链接失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.add-industry {
  max-width: 800px;
  margin: 0 auto;
}

.test-result {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 16px;
  background-color: #fafafa;
  margin-top: 8px;
}

.test-result h4 {
  margin: 8px 0 12px 0;
  color: #333;
}

:deep(.arco-descriptions-item-label) {
  width: 120px;
}
</style>