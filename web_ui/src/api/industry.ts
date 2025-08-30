import http from './http'

export interface Industry {
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

export interface IndustryListResult {
  code: number
  data: {
    list: Industry[]
    total: number
  }
}

export interface AddIndustryParams {
  name: string
  url: string
  avatar: string
  description?: string
}

export interface IndustryItem {
  url: string
  name: string
  avatar: string
}

export interface IndustrySearchResult {
  code: number
  data: IndustryItem[]
}

export const getIndustries = (params?: { page?: number; pageSize?: number }) => {
  const apiParams = {
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10
  }
  return http.get<IndustryListResult>('wx/industries', { params: apiParams })
}

export const getIndustryDetail = (industry_id: string) => {
  return http.get<{code: number, data: Industry}>(`wx/industries/${industry_id}`)
}

// 添加行业动态链接信息
export const addIndustry = (data: AddIndustryParams) => {
  return http.post<{code: number, message: string}>('wx/industries', data)
}

export const deleteIndustryApi = (industry_id: string) => {
  return http.delete<{code: number, message: string}>(`wx/industries/${industry_id}`)
}

export const deleteIndustry = (industry_id: string) => {
  return http.delete<{code: number, message: string}>(`wx/industries/${industry_id}`)
}

// 更新行业动态链接内容 
export const updateIndustries = (industry_id: string, params: { start_page?: number; end_page?: number }) => {
   const apiParams = {
    start_page: (params?.start_page || 0),
    end_page: params?.end_page || 1
  }
  return http.get<{code: number, message: string}>(`wx/industries/update/${industry_id||'all'}?start_page=${apiParams.start_page}&end_page=${apiParams.end_page}`)
}

// 更新行业动态链接信息
export const updateIndustry = (industry_id: string, data: Partial<Industry>) => {
  return http.put<{code: number, message: string}>(`wx/industries/${industry_id}`, data)
}

export const searchIndustries = (kw: string, params: { page?: number; pageSize?: number }) => {
  const apiParams = {
    kw: kw || "",
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10
  }
  return http.get<IndustryListResult>(`wx/industries`, { params: apiParams })
}

// 导出行业
export const exportIndustries = () => {
  return http.get<Blob>('wx/industries/export', { responseType: 'blob' })
}

// 导入行业
export const importIndustries = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return http.post<{code: number, message: string}>('wx/industries/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 测试行业动态网站爬虫
export const testIndustryCrawl = (url: string, maxArticles: number = 10) => {
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
  }>('wx/industries/crawl-test', { url, max_articles: maxArticles })
}