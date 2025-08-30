import http from './http'

export interface Patent {
  id: string
  url: string
  name: string
  avatar: string
  description?: string
  status: number
  sync_time: string
  rss_url: string
  article_count: number
}

export interface PatentListResult {
  code: number
  data: {
    list: Patent[]
    total: number
  }
}

export interface AddPatentParams {
  name: string
  url: string
  avatar: string
  description?: string
}

export interface PatentItem {
  url: string
  name: string
  avatar: string
}

export interface PatentSearchResult {
  code: number
  data: PatentItem[]
}

export const getPatents = (params?: { page?: number; pageSize?: number }) => {
  const apiParams = {
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10
  }
  return http.get<PatentListResult>('wx/patents', { params: apiParams })
}

export const getPatentDetail = (patent_id: string) => {
  return http.get<{code: number, data: Patent}>(`wx/patents/${patent_id}`)
}

// 添加专利检索链接信息
export const addPatent = (data: AddPatentParams) => {
  return http.post<{code: number, message: string}>('wx/patents', data)
}

export const deletePatentApi = (patent_id: string) => {
  return http.delete<{code: number, message: string}>(`wx/patents/${patent_id}`)
}

export const deletePatent = (patent_id: string) => {
  return http.delete<{code: number, message: string}>(`wx/patents/${patent_id}`)
}

// 更新专利检索链接内容 
export const updatePatents = (patent_id: string, params: { start_page?: number; end_page?: number }) => {
   const apiParams = {
    start_page: (params?.start_page || 0),
    end_page: params?.end_page || 1
  }
  return http.get<{code: number, message: string}>(`wx/patents/update/${patent_id||'all'}?start_page=${apiParams.start_page}&end_page=${apiParams.end_page}`)
}

// 更新专利检索链接信息
export const updatePatent = (patent_id: string, data: Partial<Patent>) => {
  return http.put<{code: number, message: string}>(`wx/patents/${patent_id}`, data)
}

export const searchPatents = (kw: string, params: { page?: number; pageSize?: number }) => {
  const apiParams = {
    kw: kw || "",
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10
  }
  return http.get<PatentListResult>(`wx/patents`, { params: apiParams })
}

// 导出专利
export const exportPatents = () => {
  return http.get<Blob>('wx/patents/export', { responseType: 'blob' })
}

// 导入专利
export const importPatents = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return http.post<{code: number, message: string}>('wx/patents/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 测试专利网站爬虫
export const testPatentCrawl = (url: string, maxArticles: number = 10) => {
  return http.post<{
    code: number,
    data: {
      website_info: {
        url: string
        title: string
        description: string
      },
      crawl_success: boolean
      articles_found: number
      articles: Array<{
        title: string
        url: string
        extracted_at: string
      }>
      error: string | null
    }
  }>('wx/patents/crawl-test', { url, max_articles: maxArticles })
}