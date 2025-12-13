<template>
  <div class="page-container">
    <h2>Trace Parcel</h2>
    <div class="search-bar">
      <el-input
        v-model="trackingNumber"
        placeholder="Enter Tracking Number"
        style="width: 300px; margin-right: 10px;"
      />
      <el-button type="primary" @click="handleTrace">Trace</el-button>
    </div>

    <div v-if="parcelData" class="result-container">
      <el-descriptions title="Parcel Info" border>
        <el-descriptions-item label="Tracking Number">{{ parcelData.tracking_number }}</el-descriptions-item>
        <el-descriptions-item label="Status">
          <el-tag>{{ parcelData.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Current Station">{{ parcelData.current_station_id }}</el-descriptions-item>
        <el-descriptions-item label="Next Station">{{ parcelData.next_station_id }}</el-descriptions-item>
        <el-descriptions-item label="Weight">{{ parcelData.weight }} kg</el-descriptions-item>
        <el-descriptions-item label="Volume">{{ parcelData.volume }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px;">
        <h3>Tracking History</h3>
        <el-timeline>
          <el-timeline-item
            v-for="(log, index) in parcelData.logs"
            :key="index"
            :timestamp="formatDate(log.created_at)"
            placement="top"
          >
            <el-card>
              <h4>{{ log.action }}</h4>
              <p>{{ log.description }}</p>
              <p v-if="log.station_id">Station ID: {{ log.station_id }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { traceParcel } from '@/api/logistics'
import { ElMessage } from 'element-plus'

const trackingNumber = ref('')
const parcelData = ref(null)

const handleTrace = async () => {
  if (!trackingNumber.value) {
    ElMessage.warning('Please enter a tracking number')
    return
  }
  try {
    const res = await traceParcel(trackingNumber.value)
    parcelData.value = res
  } catch (error) {
    ElMessage.error('Parcel not found or error tracing')
    parcelData.value = null
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString()
}
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.search-bar {
  margin-bottom: 20px;
}
.result-container {
  margin-top: 20px;
}
</style>
