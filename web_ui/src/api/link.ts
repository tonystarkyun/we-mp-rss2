import http from './http'

export interface Link {
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

export interface LinkListResult {
  code: number
  data: {
    list: Link[]
    total: number
  }
}

export interface AddLinkParams {
  name: string
  url: string
  avatar: string
  description?: string
}

export interface LinkItem {
  url: string
  name: string
  avatar: string
}

export interface LinkSearchResult {
  code: number
  data: LinkItem[]
}

export const getLinks = (params?: { page?: number; pageSize?: number }) => {
  const apiParams = {
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10
  }
  return http.get<LinkListResult>('wx/links', { params: apiParams })
}

export const getLinkDetail = (link_id: string) => {
  return http.get<{code: number, data: Link}>(`wx/links/${link_id}`)
}

// 添加订阅链接信息
export const addLink = (data: AddLinkParams) => {
  return http.post<{code: number, message: string}>('wx/links', data)
}

export const deleteLinkApi = (link_id: string) => {
  return http.delete<{code: number, message: string}>(`wx/links/${link_id}`)
}

export const deleteLink = (link_id: string) => {
  return http.delete<{code: number, message: string}>(`wx/links/${link_id}`)
}

// 更新订阅链接内容 
export const updateLinks = (link_id: string, params: { start_page?: number; end_page?: number }) => {
   const apiParams = {
    start_page: (params?.start_page || 0),
    end_page: params?.end_page || 1
  }
  return http.get<{code: number, message: string}>(`wx/links/update/${link_id||'all'}?start_page=${apiParams.start_page}&end_page=${apiParams.end_page}`)
}

// 更新订阅链接信息
export const updateLink = (link_id: string, data: Partial<Link>) => {
  return http.put<{code: number, message: string}>(`wx/links/${link_id}`, data)
}

export const searchLinks = (kw: string, params: { page?: number; pageSize?: number }) => {
  const apiParams = {
    kw: kw || "",
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10
  }
  return http.get<LinkListResult>(`wx/links`, { params: apiParams })
}

// 导出链接
export const exportLinks = () => {
  return http.get<Blob>('wx/links/export', { responseType: 'blob' })
}

// 导入链接
export const importLinks = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return http.post<{code: number, message: string}>('wx/links/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 测试网站爬虫
export const testWebsiteCrawl = (url: string, maxArticles: number = 10) => {
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
  }>('wx/links/crawl-test', { url, max_articles: maxArticles })
}