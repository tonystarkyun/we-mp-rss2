import http from './http'
export const ExportOPML = () => {
  return http.get<{code: number, data: string}>('/wx/export/mps/opml', {
    params: {
      limit: 1000,
      offset: 0
    }
  })
}

export const ExportMPS = () => {
  return http.get<{code: number, data: string}>('/wx/export/mps/export', {
    params: {
      limit: 1000,
      offset: 0
    }
  })
}

export const ImportMPS = (formData) => {
  return http.post<{code: number, data: string}>('/wx/export/mps/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}