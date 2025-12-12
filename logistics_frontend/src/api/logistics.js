import request from '@/utils/request'

// --- 3.1 揽收 ---
export function createParcel(data) {
  return request({
    url: '/parcels',
    method: 'post',
    data
  })
}

export function getParcelTrace(trackingNumber) {
  return request({
    url: `/parcels/${trackingNumber}/trace`,
    method: 'get'
  })
}

// --- 3.4 快递员 ---
export function getCourierTasks() {
  return request({
    url: '/courier/my-tasks',
    method: 'get'
  })
}

export function submitDeliveryResult(trackingNumber, data) {
  return request({
    url: `/delivery-tasks/${trackingNumber}/result`,
    method: 'post',
    data
  })
}