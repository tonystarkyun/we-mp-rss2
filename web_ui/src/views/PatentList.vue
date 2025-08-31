<template>
  <a-spin :loading="fullLoading" tip="正在刷新..." size="large">
  <a-layout class="patent-list">
    <a-layout-sider :width=300
      :style="{ background: '#fff', padding: '0', borderRight: '1px solid #eee', display: 'flex', flexDirection: 'column' ,border:0}">
      <a-card :bordered="false" title="专利检索" 
        :headStyle="{ padding: '12px 16px', borderBottom: '1px solid #eee', background: '#fff', zIndex: 1 ,border:0}">
        <template #extra>
           <a-dropdown>
              <a-button type="primary">
                <template #icon><icon-plus  /></template>
                专利
                <icon-down />
              </a-button>
              <template #content>
                <a-doption @click="showAddModal"><template #icon><icon-plus /></template>添加专利</a-doption>
                <!-- <a-doption @click="exportPatents"><template #icon><icon-export /></template>导出专利</a-doption>
                <a-doption @click="importPatents"><template #icon><icon-import /></template>导入专利</a-doption>
                <a-doption @click="exportOPML"><template #icon><icon-share-external /></template>导出OPML</a-doption> -->
              </template>
            </a-dropdown>
        </template>
        <div style="display: flex; flex-direction: column;; background: #fff">
            <a-list :data="patentList" :loading="patentLoading" bordered>
              <template #item="{ item, index }">
                <a-list-item @click="handlePatentClick(item.id)" :class="{ 'active-patent': activePatentId === item.id }"
                  style="padding: 9px 8px; cursor: pointer; display: flex; align-items: center; justify-content: space-between;">
                 <div style="display: flex; align-items: center;">
                   <img :src="Avatar(item.avatar)" width="40" style="float:left;margin-right:1rem;"/>
                   <a-typography-text  strong style="line-height:32px;">
                     {{ item.name || item.url }}
                   </a-typography-text>
                   <a-button v-if="activePatentId === item.id && item.id!=''" size="mini" type="text" status="danger" @click="$event.stopPropagation(); deletePatent(item.id)" >
                     <template #icon><icon-delete /></template>
                    </a-button>
                  </div>
                </a-list-item>
              </template>
            </a-list>
            <a-pagination :total="patentPagination.total" simple  @change="handlePatentPageChange" :show-total="true" style="margin-top: 1rem;"/>
        </div>
      </a-card>
    </a-layout-sider>

    <a-layout-content :style="{ padding: '20px', width: '100%'}" >
      <a-page-header 
      :title="activeFeed ? activeFeed.name : '全部'" 
      :subtitle="'管理您的专利检索内容'" :show-back="false">
          <template #extra>
          <a-space>
            <a-button @click="refresh" v-if="activeFeed?.id!=''">
              <template #icon><icon-refresh /></template>
              刷新
            </a-button>
          </a-space>
        </template>
      </a-page-header>

      <a-modal 
        v-model:visible="refreshModalVisible" 
        title="设置刷新范围"
        @ok="handleRefresh"
        @cancel="refreshModalVisible = false"
      >
        <a-form :model="refreshForm" :rules="refreshRules">
          <a-form-item field="startPage" label="开始页码">
            <a-input-number v-model="refreshForm.startPage" :min="1" />
          </a-form-item>
          <a-form-item field="endPage" label="结束页码">
            <a-input-number v-model="refreshForm.endPage" :min="refreshForm.startPage" />
          </a-form-item>
        </a-form>
      </a-modal>

      <a-card style="border:0">
        <div class="search-bar">
          <a-input-search v-model="searchText" placeholder="搜索文章标题" @search="handleSearch" @keyup.enter="handleSearch" allow-clear />
        </div>

        <ResponsiveTable 
          :columns="columns" 
          :data="articles" 
          :loading="loading" 
          :pagination="pagination" 
          :row-selection="{
            type: 'checkbox',
            showCheckedAll: true,
            width: 50,
            fixed: true
          }"
          row-key="id"
          @page-change="handlePageChange"
          v-model:selectedKeys="selectedRowKeys"
        >
          <template #status="{ record }">
            <a-tag :color="statusColorMap[record.status]">
              {{ statusTextMap[record.status] }}
            </a-tag>
          </template>
          <template #actions="{ record }">
            <a-space>
              <a-button type="text" @click="viewArticle(record)" :title="record.id">
                <template #icon><icon-eye /></template>
              </a-button>
              <a-button type="text" status="danger" @click="deleteArticle(record.id)">
                <template #icon><icon-delete /></template>
              </a-button>
            </a-space>
          </template>
        </ResponsiveTable>

        <a-drawer 
          v-model:visible="articleModalVisible" 
          :title="currentArticle.title"
          placement="left"
          width="70vw"
          :footer="false"
          :fullscreen="false"
        >
          <div style="padding: 20px;  overflow-y: auto">
            <div v-html="currentArticle.content"></div>
            <div style="margin-top: 20px; color: var(--color-text-3); text-align: right">
              {{ currentArticle.time }}
            </div>
          </div>
        </a-drawer>
      </a-card>
    </a-layout-content>
  </a-layout>
</a-spin>
</template>

<script setup lang="ts">
import { Avatar } from '@/utils/constants'
import { ref, onMounted, h } from 'vue'
import axios from 'axios'
import { IconApps, IconAtt, IconDelete, IconEdit, IconEye, IconRefresh, IconScan, IconWeiboCircleFill, IconWifi, IconCode} from '@arco-design/web-vue/es/icon'
import ResponsiveTable from '@/components/ResponsiveTable.vue'
import { getArticles,deleteArticle as deleteArticleApi ,ClearArticle,ClearDuplicateArticle,getArticleDetail } from '@/api/article'
import { getPatents, updatePatents, deletePatentApi, exportPatents as exportPatentsApi, importPatents as importPatentsApi } from '@/api/patent'
import { inject } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { formatDateTime,formatTimestamp } from '@/utils/date'
import router from '@/router'
import TextIcon from '@/components/TextIcon.vue'
const articles = ref([])
const loading = ref(false)
const patentList = ref([])
const patentLoading = ref(false)
const activePatentId = ref('')
const selectedRowKeys = ref([])
const patentPagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
  showPageSize: false,
  showJumper: false,
  showTotal: true,
  pageSizeOptions: [5, 10, 15]
})
const searchText = ref('')
const filterStatus = ref('')

const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
  showTotal: true,
  showJumper: true,
  showPageSize: true,
  pageSizeOptions: [10]
})

const statusTextMap = {
  published: '已发布',
  draft: '草稿',
  deleted: '已删除'
}

const statusColorMap = {
  published: 'green',
  draft: 'orange',
  deleted: 'red'
}

const columns = [
  {
    title: '文章标题',
    dataIndex: 'title',
    width: window.innerWidth -1000,
    ellipsis: true,
    render: ({ record }) => h('a', {
      href: record.url || '#',
      title: record.title,
      target: '_blank',
      style: { color: 'var(--color-text-1)' }
    }, record.title)
  },
  {
    title: '来源',
    dataIndex: 'source',
    width: '120',
    ellipsis: true,
    render: ({ record }) => {
      return h('span', {
        style: { color: 'var(--color-text-3)' }
      }, '专利文章')
    }
  },
  {
    title: '更新时间',
    dataIndex: 'created_at',
    width: '140',
    render: ({ record }) => h('span',
      { style: { color: 'var(--color-text-3)', fontSize: '12px' } },
      formatDateTime(record.created_at)
    )
  },
  {
    title: '发布时间',
    dataIndex: 'publish_time',
    width: '140',
    render: ({ record }) => h('span',
      { style: { color: 'var(--color-text-3)', fontSize: '12px' } },
      formatTimestamp(record.publish_time)
    )
  },
  {
    title: '操作',
    dataIndex: 'actions',
    slotName: 'actions'
  }
]

const handlePatentPageChange = (page: number, pageSize: number) => {
  patentPagination.value.current = page
  patentPagination.value.pageSize = pageSize
  fetchPatentList()
}
const rssFormat = ref('atom')
const activeFeed=ref({
  id:"",
  name:"全部",
})
const handlePatentClick = (patentId: string) => {
  activePatentId.value = patentId
  pagination.value.current = 1
  activeFeed.value=patentList.value.find(item => item.id === activePatentId.value)
  console.log(activeFeed.value)

  fetchArticles()
}

const fetchArticles = async () => {
  loading.value = true
  try {
    console.log('请求参数:', {
      page: pagination.value.current - 1,
      pageSize: pagination.value.pageSize,
      search: searchText.value,
      status: filterStatus.value,
      patent_id: activePatentId.value
    })

    const res = await getArticles({
      page: pagination.value.current - 1,
      pageSize: pagination.value.pageSize,
      search: searchText.value,
      status: filterStatus.value,
      patent_id: activePatentId.value
    })

    // 确保数据包含必要字段
    articles.value = (res.list || []).map(item => ({
      ...item,
      mp_name: item.mp_name || item.account_name || '专利文章',
      publish_time: item.publish_time || item.create_time || '-',
      url: item.url||"#"
    }))
    pagination.value.total = res.total || 0
  } catch (error) {
    console.error('获取文章列表错误:', error)
    Message.error(error)
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number, pageSize: number, type?: string) => {
  console.log('分页事件触发:', {page, pageSize, type})
  pagination.value.current = page
  pagination.value.pageSize = pageSize
  fetchArticles()
}

const handleSearch = () => {
  pagination.value.current = 1
  fetchArticles()
}

const wechatAuthQrcodeRef = ref()
  const showAuthQrcode = inject('showAuthQrcode') as () => void
  const handleAuthClick = () => {
    showAuthQrcode()
  }

const exportOPML = async () => {
  try {
    const response = await ExportOPML();
    const blob = new Blob([response], { type: 'application/xml' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'rss_feed.opml';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('导出OPML失败:', error);
    Message.error(error?.message || '导出OPML失败');
  }
};
const exportPatents = async () => {
  try {
    const response = await exportPatentsApi();
    const blob = new Blob([response], { type: 'application/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = '专利列表.csv';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    Message.error(error?.message || '导出专利失败');
  }
};

const importPatents = async () => {
  try {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const formData = new FormData();
      formData.append('file', file);
      const response = await importPatentsApi(file);
      Message.info(response?.message || "导入成功");
    };
    input.click();
  } catch (error) {
    Message.error(error?.message || '导入专利失败');
  }
};

const openRssFeed = () => {
  const format = ['rss', 'atom', 'json','md','txt'].includes(rssFormat.value) 
    ? rssFormat.value 
    : 'atom'
  let search=""
  if(searchText.value!=""){
    search="/search/"+searchText.value;
  }
  if (!activePatentId.value) {
    window.open(`/feed${search}/all.${format}`, '_blank')
    return
  }
  const activePatent = patentList.value.find(item => item.id === activePatentId.value)
  if (activePatent) {
    window.open(`/feed${search}/${activePatentId.value}.${format}`, '_blank')
  }
}

const fullLoading = ref(false)

const refreshModalVisible = ref(false)
const refreshForm = ref({
  startPage: 0,
  endPage: 1
})
const refreshRules = {
  startPage: [{ required: true, message: '请输入开始页码' }],
  endPage: [{ required: true, message: '请输入结束页码' }]
}

const showRefreshModal = () => {
  refreshModalVisible.value = true
}

const handleRefresh = () => {
  fullLoading.value = true
  updatePatents(activePatentId.value, {
    start_page: refreshForm.value.startPage,
    end_page: refreshForm.value.endPage
  }).then(() => {
    Message.success('刷新成功')
    refreshModalVisible.value = false
  }).finally(() => {
    fullLoading.value = false
  })
  fetchArticles()
}

const refresh = () => {
  showRefreshModal()
}

const showAddModal = () => {
  router.push('/add-patent')
}

const handleAddSuccess = () => {
  fetchArticles()
}

const viewArticle = async (_record: any) => {
  loading.value = true;
  let record=await getArticleDetail(_record?.id)
  let source_tpl=`<a href="${record.url}" target="_blank">查看原文</a>`
  if (record.content) {
    // 处理图片链接，在所有图片链接前加上/static/res/logo/
    const processedContent = source_tpl+record.content.replace(
      /(<img[^>]*src=["'])(?!\/static\/res\/logo\/)([^"']*)/g,
      '$1/static/res/logo/$2'
    )
    currentArticle.value = {
      title: record.title,
      content: processedContent,
      time: formatDateTime(record.created_at),
      url: record.url
    }
    articleModalVisible.value = true
  } else {
    currentArticle.value = {
      title: record.title,
      content: source_tpl,
      time: formatDateTime(record.created_at),
      url: record.url
    }
    articleModalVisible.value = true
  }
  loading.value = false;
}

const currentArticle = ref({
  title: '',
  content: '',
  time: '',
  url: ''
})
const articleModalVisible = ref(false)

const deleteArticle = (id: number) => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除该文章吗？删除后将无法恢复。',
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      await deleteArticleApi(id);
      Message.success('删除成功');
      fetchArticles();
    },
    onCancel: () => {
      Message.info('已取消删除操作');
    }
  });
}

const handleBatchDelete = () => {
  Modal.confirm({
    title: '确认批量删除',
    content: `确定要删除选中的${selectedRowKeys.value.length}篇文章吗？删除后将无法恢复。`,
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await Promise.all(selectedRowKeys.value.map(id => deleteArticleApi(id)));
        Message.success(`成功删除${selectedRowKeys.value.length}篇文章`);
        selectedRowKeys.value = [];
        fetchArticles();
      } catch (error) {
        Message.error('删除部分文章失败');
      }
    },
    onCancel: () => {
      Message.info('已取消批量删除操作');
    }
  });
}

onMounted(() => {
  console.log('专利检索组件挂载，开始获取数据')
  // 重置状态
  activePatentId.value = ''
  activeFeed.value = {
    id: "",
    name: "全部",
  }
  
  fetchPatentList().then(() => {
    console.log('专利列表获取完成')
    fetchArticles()
  }).catch(err => {
    console.error('初始化失败:', err)
  })
})

const fetchPatentList = async () => {
  patentLoading.value = true
  try {
    const res = await getPatents({
      page: patentPagination.value.current - 1,
      pageSize: patentPagination.value.pageSize
    })
    
    // 调试响应结构
    console.log('专利API响应:', res)
    console.log('响应结构:', JSON.stringify(res, null, 2))
    
    // 适配不同的响应结构
    const listData = res.list || res.data?.list || []
    const totalCount = res.total || res.data?.total || 0
    
    patentList.value = listData.map(item => ({
      id: item.id || item.url,
      name: item.name || item.url,
      avatar: item.avatar || '/static/logo.svg',
      description: item.description || '',
      article_count: item.article_count || 0
    }))
    // 添加'全部'选项
    patentList.value.unshift({
      id: '',
      name: '全部',
      avatar: '/static/logo.svg',
      description: '显示所有专利文章',
      article_count: totalCount
    });
    patentPagination.value.total = totalCount
  } catch (error) {
    console.error('获取专利列表错误:', error)
  } finally {
    patentLoading.value = false
  }
}
const deletePatent = async (patentId: string) => {
  try {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除该专利链接吗？删除后将无法恢复。',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        await deletePatentApi(patentId);
        Message.success('专利链接删除成功');
        fetchPatentList();
      },
      onCancel: () => {
        Message.info('已取消删除操作');
      }
    });
  } catch (error) {
    console.error('删除专利链接失败:', error);
    Message.error('删除专利链接失败，请稍后重试');
  }
}

const importArticles = () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.json';
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;

    try {
      const content = await file.text();
      const data = JSON.parse(content);
      // 这里应该调用API导入数据
      Message.success(`成功导入${data.length}篇文章`);
    } catch (error) {
      console.error('导入文章失败:', error);
      Message.error('导入失败，请检查文件格式');
    }
  };
  input.click();
};

const exportArticles = () => {
  if (!articles.value.length) {
    Message.warning('没有文章可导出');
    return;
  }

  const data = JSON.stringify(articles.value, null, 2);
  const blob = new Blob([data], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `articles_${activePatentId.value || 'all'}_${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  Message.success('导出成功');
};
</script>

<style scoped>
.article-list {
  /* height: calc(100vh - 186px); */
}

.a-layout-sider {
  overflow: hidden;
}

.a-list-item {
  cursor: pointer;
  padding: 12px 16px;
  transition: all 0.2s;
  margin-bottom:0 !important;
}

.a-list-item:hover {
  background-color: var(--color-fill-2);
}

.active-mp {
  background-color: var(--color-primary-light-1);
}

.active-patent {
  background-color: var(--color-primary-light-1);
}

.search-bar {
  display: flex;
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .a-layout-sider {
    width: 100% !important;
    max-width: 100%;
  }

  .a-layout {
    flex-direction: column;
  }
}

.arco-drawer-body {
  z-index: 9999 !important; /* 确保抽屉在其他内容之上 */
}
</style>