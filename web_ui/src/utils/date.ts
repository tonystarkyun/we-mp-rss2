import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

// 加载时区插件
dayjs.extend(utc)
dayjs.extend(timezone)

export const formatDateTime = (date: string | Date | undefined) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

export const formatTimestamp = (timestamp: number | undefined) => {
  if (!timestamp) return '-'
  
  // 处理Unix时间戳（秒级或毫秒级）
  const timestampLength = timestamp.toString().length;
  const adjustedTimestamp = timestampLength <= 10 ? timestamp * 1000 : timestamp;
  
  // 后端存储的是UTC时间戳，需要转换为本地时区显示
  // 使用 dayjs 的时区功能确保正确转换
  return dayjs(adjustedTimestamp).format('YYYY-MM-DD HH:mm')
}
