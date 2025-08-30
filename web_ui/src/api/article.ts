import http from './http'

export interface Article {
  id: number
  title: string
  content: string
  mp_name: string
  publish_time: string
  status: number
  link: string
  created_at: string
}

export interface ArticleListParams {
  offset?: number
  limit?: number
  search?: string
  status?: number
  mp_id?: string
  link_id?: string
  patent_id?: string
  industry_id?: string
}

export interface ArticleListResult {
  code: number
  data: Article[]
}

export const getArticles = (params: ArticleListParams) => {
  // 转换分页参数
  const apiParams = {
    offset: (params.page || 0) * (params.pageSize || 10),
    limit: params.pageSize || 10,
    search: params.search,
    status: params.status,
    mp_id: params.mp_id,
    link_id: params.link_id,
    patent_id: params.patent_id,
    industry_id: params.industry_id
  }
  return http.get<ArticleListResult>('/wx/articles', { 
    params: apiParams 
  })
}

export const getArticleDetail = (id: number) => {
  return http.get<{code: number, data: Article}>(`/wx/articles/${id}`)
}

export const deleteArticle = (id: number) => {
  return http.delete<{code: number, message: string}>(`/wx/articles/${id}`)
}
export const ClearArticle = (id: number) => {
  return http.delete<{code: number, message: string}>(`/wx/articles/clean`)
}
export const ClearDuplicateArticle = (id: number) => {
  return http.delete<{code: number, message: string}>(`/wx/articles/clean_duplicate_articles`)
}

