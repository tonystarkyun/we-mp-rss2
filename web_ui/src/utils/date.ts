import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

// 加载时区插件
dayjs.extend(utc)
dayjs.extend(timezone)

export const formatDateTime = (date: string | Date | undefined) => {
  if (!date) return '-'
  
  // 简单处理：直接显示时间
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

// 专门用于爬虫数据的时间格式化（加8小时）
export const formatCrawlerDateTime = (date: string | Date | undefined) => {
  if (!date) return '-'
  
  // 爬虫数据（UTC时间），加8小时转换为中国本地时间
  return dayjs(date).add(8, 'hour').format('YYYY-MM-DD HH:mm')
}

export const formatTimestamp = (timestamp: number | string | undefined) => {
  if (!timestamp || timestamp === '' || timestamp === '0') return '-'
  
  // 转换为数字类型
  let numTimestamp: number;
  if (typeof timestamp === 'string') {
    numTimestamp = parseInt(timestamp);
    if (isNaN(numTimestamp) || numTimestamp <= 0) return '-'
  } else {
    numTimestamp = timestamp;
  }
  
  // 处理Unix时间戳（秒级或毫秒级）
  const timestampLength = numTimestamp.toString().length;
  const adjustedTimestamp = timestampLength <= 10 ? numTimestamp * 1000 : numTimestamp;
  
  // 验证时间戳是否有效
  const date = new Date(adjustedTimestamp);
  if (isNaN(date.getTime())) return '-'
  
  // 后端存储的是本地时间戳，直接显示即可
  return dayjs(adjustedTimestamp).format('YYYY-MM-DD HH:mm')
}
