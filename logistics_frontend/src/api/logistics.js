import request from '@/utils/request'

// Auth
export function login(data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

// Parcels
export function createParcel(data) {
  return request({
    url: '/parcels/',
    method: 'post',
    data
  })
}

export function traceParcel(trackingNumber) {
  return request({
    url: '/parcels/trace',
    method: 'get',
    params: { tracking_number: trackingNumber }
  })
}

// Transport
export function createTransportTask(data) {
  return request({
    url: '/transport/start',
    method: 'post',
    data
  })
}

export function updateTransportStatus(data) {
  return request({
    url: '/transport/status',
    method: 'put',
    data
  })
}

// Delivery
export function createDeliveryTask(data) {
  return request({
    url: '/delivery/start',
    method: 'post',
    data
  })
}

export function updateDeliveryStatus(data) {
  return request({
    url: '/delivery/status',
    method: 'put',
    data
  })
}
