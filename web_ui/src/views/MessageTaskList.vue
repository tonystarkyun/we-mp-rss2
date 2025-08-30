<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listMessageTasks, deleteMessageTask,FreshJobApi,FreshJobByIdApi,RunMessageTask } from '@/api/messageTask'
import type { MessageTask } from '@/types/messageTask'
import { useRouter } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'

const parseCronExpression = (exp: string) => {
  const parts = exp.split(' ')
  if (parts.length !== 5) return exp
  
  const [minute, hour, day, month, week] = parts
  
  let result = ''
  
  // 解析分钟
  if (minute === '*') {
    result += '每分钟'
  } else if (minute.includes('/')) {
    const [_, interval] = minute.split('/')
    result += `每${interval}分钟`
  } else {
    result += `在${minute}分`
  }
  
  // 解析小时
  if (hour === '*') {
    result += '每小时'
  } else if (hour.includes('/')) {
    const [_, interval] = hour.split('/')
    result += `每${interval}小时`
  } else {
    result += ` ${hour}时`
  }
  
  // 解析日期
  if (day === '*') {
    result += ' 每天'
  } else if (day.includes('/')) {
    const [_, interval] = day.split('/')
    result += ` 每${interval}天`
  } else {
    result += ` ${day}日`
  }
  
  // 解析月份
  if (month === '*') {
    result += ' 每月'
  } else if (month.includes('/')) {
    const [_, interval] = month.split('/')
    result += ` 每${interval}个月`
  } else {
    result += ` ${month}月`
  }
  
  // 解析星期
  if (week !== '*') {
    result += ` 星期${week}`
  }
  
  return result || exp
}

const router = useRouter()
const loading = ref(false)
const taskList = ref<MessageTask[]>([])
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0
})

const fetchTaskList = async () => {
  loading.value = true
  try {
    const res = await listMessageTasks({
      offset: (pagination.value.current - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    })
    taskList.value = res.list
    pagination.value.total = res.total
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  pagination.value.current = page
  fetchTaskList()
}

const handleAdd = () => {
  router.push('/message-tasks/add')
}
const FreshJob = () => {
  FreshJobApi().then((data) => {
    console.log("刷新任务")
    Message.success(data.message||"刷新任务成功")
  })
}

const handleEdit = (id: number) => {
  router.push(`/message-tasks/edit/${id}`)
}

const handleView = (id: number) => {
  router.push(`/message-tasks/detail/${id}`)
}

const handleDelete = async (id: number) => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这条消息任务吗？删除后无法恢复',
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteMessageTask(id)
        Message.success('删除成功')
        fetchTaskList()
      } catch (error) {
        console.error(error)
        Message.error('删除失败')
      }
    }
  })
}
const runTask = async (id: number,isTest:boolean=false) => {
  Modal.confirm({
    title: '确认执行',
    content: '确定要执行这条消息任务吗？',
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        let res = await RunMessageTask(id,isTest)
        Message.success(res?.message||'执行成功')
      } catch (error) {
        console.error(error)
        Message.error('执行失败')
        console.log(error)
      }
    }
  })
}

onMounted(() => {
  fetchTaskList()
})
</script>

<template>
  <a-spin :loading="loading">
    <div class="message-task-list">
      <div class="header">
        <h2>消息任务列表</h2>
        <a-tooltip content="点击应用按钮后任务才会生效">
          <a-button type="primary" @click="FreshJob">应用</a-button>
        </a-tooltip>
        <a-button type="primary" @click="handleAdd">添加消息任务</a-button>
      </div>
      <a-alert type="info" closable>
        注意：只有添加了任务消息才会定时执行更新任务，点击应用按钮后任务才会生效
      </a-alert>

      <a-table
        :data="taskList"
        :pagination="pagination"
        @page-change="handlePageChange"
      >
        <template #columns>
          <!-- <a-table-column title="ID" data-index="id" /> -->
          <a-table-column title="名称" data-index="name" ellipsis :width="200"/>
          <!-- <a-table-column title="类型" data-index="message_type" ellipsis /> -->
          <a-table-column title="cron表达式">
            <template #cell="{ record }">
              {{ parseCronExpression(record.cron_exp) }}
            </template>
          </a-table-column>
          <a-table-column title="类型" :width="100">
            <template #cell="{ record }">
              <a-tag :color="record.message_type === 1 ? 'green' : 'red'">
                {{ record.message_type === 1 ? 'WeekHook' : 'Message' }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="状态" :width="100">
            <template #cell="{ record }">
              <a-tag :color="record.status === 1 ? 'green' : 'red'">
                {{ record.status === 1 ? '启用' : '禁用' }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="操作" :width="260">
            <template #cell="{ record }">
              <a-space>
                <a-button size="mini" type="primary" @click="handleEdit(record.id)">编辑</a-button>
                <a-tooltip content="点击测试消息任务">
                  <a-button size="mini" type="dashed" @click="runTask(record.id,true)">测试</a-button>
                </a-tooltip>
                <a-tooltip content="执行更新任务">
                  <a-button size="mini" type="dashed" @click="runTask(record.id)">执行</a-button>
                </a-tooltip>
                <a-button size="mini" status="danger" @click="handleDelete(record.id)">删除</a-button>
              </a-space>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </div>
  </a-spin>
</template>

<style scoped>
.message-task-list {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  flex: 1;
}

.header .arco-btn {
  margin-left: 10px;
}

h2 {
  margin: 0;
  color: var(--color-text-1);
}
</style>