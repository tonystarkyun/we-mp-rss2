<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listTags, deleteTag } from '@/api/tagManagement'
import type { Tag } from '@/types/tagManagement'
import { Message } from '@arco-design/web-vue'

const loading = ref(false)
const tags = ref<Tag[]>([])
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0
})

const fetchTags = async () => {
  try {
    loading.value = true
    const res = await listTags({
      skip: (pagination.value.current - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    })
    console.log(res)
    tags.value = res.list||[]
    pagination.value.total = res.total || 0
  } catch (error) {
    Message.error('获取标签列表失败')
  } finally {
    loading.value = false
  }
}

const handleDelete = async (id: string) => {
  try {
    await deleteTag(id)
    Message.success('删除成功')
    fetchTags()
  } catch (error) {
    Message.error('删除失败')
  }
}

const handlePageChange = (page: number) => {
  pagination.value.current = page
  fetchTags()
}

onMounted(() => {
  fetchTags()
})
</script>

<template>
  <div class="tag-list">
    <a-page-header title="标签管理" subtitle="管理文章标签">
      <template #extra>
        <a-button type="primary" @click="$router.push('/tags/add')">
          添加标签
        </a-button>
      </template>
    </a-page-header>

    <a-card>
      <a-table
        :loading="loading"
        :data="tags"
        :pagination="pagination"
        @page-change="handlePageChange"
      >
        <template #columns>
          <a-table-column title="标签名称" data-index="name" />
          <a-table-column title="状态" data-index="status">
            <template #cell="{ record }">
              <a-tag v-if="record.status === 1" color="green">启用</a-tag>
              <a-tag v-else color="red">禁用</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="创建时间" data-index="created_at" />
          <a-table-column title="操作">
            <template #cell="{ record }">
              <a-space>
                <a-button type="text" @click="$router.push(`/tags/edit/${record.id}`)">
                  编辑
                </a-button>
                <a-popconfirm content="确认删除该标签？" @ok="handleDelete(record.id)">
                  <a-button type="text" status="danger">删除</a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<style scoped>
.tag-list {
  padding: 16px;
}
</style>