<template>
  <div class="trace-page">
    <el-card>
      <div class="search-area">
        <el-input 
          v-model="queryCode" 
          placeholder="请输入运单号 (如 SF2025120101)" 
          class="input-with-select"
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button @click="handleSearch">🔍 查询</el-button>
          </template>
        </el-input>
      </div>

      <el-skeleton :rows="5" animated v-if="loading" />
      
      <div v-if="traceData" class="trace-content">
        <div class="trace-header">
          <h2>{{ traceData.tracking_number }}</h2>
          <el-tag :type="statusType(traceData.current_status)" size="large">
            {{ formatStatus(traceData.current_status) }}
          </el-tag>
        </div>
        
        <p class="location-info">当前位置: {{ traceData.current_location }}</p>
        <el-divider />

        <el-timeline>
          <el-timeline-item
            v-for="(log, index) in traceData.logs"
            :key="index"
            :timestamp="log.time"
            :type="index === 0 ? 'primary' : ''"
            :hollow="index === 0"
            placement="top"
          >
            <el-card shadow="hover" class="log-card">
              <h4>{{ log.desc }}</h4>
              <p>操作站点: {{ log.station }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
      
      <el-empty v-if="!traceData && !loading" description="请输入运单号查询" />
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { getParcelTrace } from '@/api/logistics'

const queryCode = ref('')
const loading = ref(false)
const traceData = ref(null)

const handleSearch = async () => {
  if (!queryCode.value) return
  loading.value = true
  traceData.value = null
  try {
    const res = await getParcelTrace(queryCode.value)
    traceData.value = res
  } catch (e) {
    // 错误处理
  } finally {
    loading.value = false
  }
}

const formatStatus = (val) => {
  const map = { created: '已下单', sorting: '分拣中', in_transit: '运输中', dispatching: '派送中', delivered: '已签收', exception: '异常' }
  return map[val] || val
}

const statusType = (val) => {
  if (val === 'delivered') return 'success'
  if (val === 'exception') return 'danger'
  return 'primary'
}
</script>

<style scoped>
.trace-page { max-width: 800px; margin: 0 auto; padding: 20px; }
.search-area { margin-bottom: 30px; }
.trace-header { display: flex; justify-content: space-between; align-items: center; }
.log-card { background-color: #fafafa; }
</style>