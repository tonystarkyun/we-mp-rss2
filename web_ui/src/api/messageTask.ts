import http from './http'
import type { MessageTask, MessageTaskUpdate } from '@/types/messageTask'

export const listMessageTasks = (params?: { page?: number; pageSize?: number }) => {
  const apiParams = {
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10
  }
  return http.get<MessageTask>('/wx/message_tasks', { params: apiParams })
}
export const getMessageTask = (id: number) => {
  return http.get<MessageTask>(`/wx/message_tasks/${id}`)
}
export const RunMessageTask = (id: number,isTest:boolean=false) => {
  return http.get<MessageTask>(`/wx/message_tasks/${id}/run?isTest=${isTest}`)
}

export const createMessageTask = (data: MessageTaskUpdate) => {
  return http.post('/wx/message_tasks', data)
}

export const updateMessageTask = (id: number, data: MessageTaskUpdate) => {
  return http.put(`/wx/message_tasks/${id}`, data)
}
export const FreshJobApi = () => {
  return http.put(`/wx/message_tasks/job/fresh`)
}
export const FreshJobByIdApi = (id: number, data: MessageTaskUpdate) => {
  return http.put(`/wx/message_tasks/job/fresh/${id}`, data)
}

export const deleteMessageTask = (id: number) => {
  return http.delete(`/wx/message_tasks/${id}`)
}