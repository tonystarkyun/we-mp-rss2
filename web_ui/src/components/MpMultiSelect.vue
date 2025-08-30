<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { searchMps } from '@/api/subscription'
import type { MpItem } from '@/types/subscription'

const formatCoverUrl = (url: string) => {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return '/static/res/logo/' + url
  }
  return url
}

const props = defineProps({
  modelValue: {
    type: Array as () => MpItem[],
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const searchKeyword = ref('')
const loading = ref(false)
const mpList = ref<MpItem[]>([])
const selectedMps = ref<MpItem[]>([])
const currentPage = ref(0)
const hasMore = ref(true)
const pageSize = 10

const filteredMps = computed(() => {
  return mpList.value.filter(mp => 
    !selectedMps.value.some(selected => selected.id === mp.id)
  )
})

const fetchMps = async (reset = true) => {
  loading.value = true
  try {
    if (reset) {
      currentPage.value = 0
      mpList.value = []
    }
    
    const res = await searchMps(searchKeyword.value, { 
      page: currentPage.value,
      pageSize: pageSize
    })
    
    // 将 API 返回的数据格式转换为组件内部使用的格式
    const mappedList = res.list.map((item: any) => ({
      id: item.mp_id || item.id,
      mp_name: item.mp_name,
      mp_cover: item.avatar || item.mp_cover
    }))
    
    // 添加新加载的数据到列表，避免覆盖已有数据
    if (reset) {
      mpList.value = mappedList
    } else {
      // 合并数据，避免重复
      const newMps = mappedList.filter(newMp => 
        !mpList.value.some(existingMp => existingMp.id === newMp.id)
      )
      mpList.value = [...mpList.value, ...newMps]
    }
    
    // 判断是否还有更多数据
    hasMore.value = res.list.length === pageSize
    
  } finally {
    loading.value = false
  }
}

const loadMore = async () => {
  currentPage.value++
  await fetchMps(false)
}

const handleSearch = () => {
  fetchMps(true)
}

const toggleSelect = (mp: MpItem) => {
  const index = selectedMps.value.findIndex(m => m.id === mp.id)
  if (index === -1) {
    selectedMps.value.push(mp)
  } else {
    selectedMps.value.splice(index, 1)
  }
  emitSelectedIds()
}

const removeSelected = (mp: MpItem) => {
  selectedMps.value = selectedMps.value.filter(m => m.id !== mp.id)
  emitSelectedIds()
}

const clearAll = () => {
  selectedMps.value = []
  emitSelectedIds()
}

const selectAll = () => {
  filteredMps.value.forEach(mp => {
    if (!selectedMps.value.some(m => m.id === mp.id)) {
      selectedMps.value.push(mp)
    }
  })
  emitSelectedIds()
}

const emitSelectedIds = () => {
  emit('update:modelValue', selectedMps.value)
}

const parseSelected = (data:MpItem[]) => {
  selectedMps.value = data.map(item => {
    const found = mpList.value.find(mp => mp.id === item.id)
    return found || {
      id: item.id,
      mp_name: item.mp_name,
      mp_cover: (item.mp_cover||'')
    }
  })
}

defineExpose({
  parseSelected
})

onMounted(() => {
  fetchMps()
  if (props.modelValue && props.modelValue.length > 0) {
    parseSelected(props.modelValue)
  }
})
</script>

<template>
  <a-card class="mp-multi-select" :bordered="false">
    <a-space direction="vertical" fill>
      <a-space>
        <a-input
          v-model="searchKeyword"
          placeholder="搜索公众号"
          allow-clear
          @press-enter="handleSearch"
        />
        <a-button type="primary" @click="handleSearch">搜索</a-button>
      </a-space>

      <a-spin :loading="loading">
        <template v-if="selectedMps.length > 0">
          <a-space align="center">
            <h4>已选公众号 ({{ selectedMps.length }})</h4>
            <a-button size="mini" type="text" @click="clearAll">清空</a-button>
          </a-space>
          <a-space wrap>
            <a-tag
              v-for="mp in selectedMps"
              :key="mp.id"
              closable
              @close="removeSelected(mp)"
            >
              <a-avatar :size="20" :image-url="formatCoverUrl(mp.mp_cover)">
                <img v-if="mp.mp_cover" :src="formatCoverUrl(mp.mp_cover)" :alt="mp.mp_name" />
              </a-avatar>
              {{ mp.mp_name }}
            </a-tag>
          </a-space>
        </template>

        <a-space align="center">
          <h4>可选公众号</h4>
          <a-button size="mini" type="text" @click="selectAll">全选</a-button>
        </a-space>
        <div class="mp-list">
          <div
            v-for="mp in filteredMps"
            :key="mp.id"
            class="mp-item"
            @click="toggleSelect(mp)"
          >
            <a-space>
              <a-avatar :size="24" :image-url="formatCoverUrl(mp.mp_cover)">
                <img v-if="mp.mp_cover" :src="formatCoverUrl(mp.mp_cover)" :alt="mp.mp_name" />
              </a-avatar>
              <span>{{ mp.mp_name }}</span>
            </a-space>
          </div>
        </div>
        
        <div v-if="hasMore" class="load-more">
          <a-button type="text" @click="loadMore" :loading="loading">
            加载更多
          </a-button>
        </div>
      </a-spin>
    </a-space>
  </a-card>
</template>

<style scoped>
.mp-multi-select {
  padding: 15px;
}

h4 {
  margin-bottom: 10px;
  font-size: 14px;
  color: var(--color-text-2);
}

:deep(.arco-list-item) {
  padding: 8px 0;
  cursor: pointer;
}

:deep(.arco-list-item:hover) {
  background-color: var(--color-fill-2);
}

.mp-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mp-item {
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  background-color: var(--color-fill-1);
}

.mp-item:hover {
  background-color: var(--color-fill-2);
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>