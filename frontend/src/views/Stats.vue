<template>
  <div v-loading="loading">
    <el-row :gutter="16" class="cards">
      <el-col :span="8">
        <el-card><div class="stat-num">{{ overview.total_visits }}</div><div class="stat-label">累计访问量</div></el-card>
      </el-col>
      <el-col :span="8">
        <el-card><div class="stat-num">{{ overview.today_visits }}</div><div class="stat-label">今日访问</div></el-card>
      </el-col>
      <el-col :span="8">
        <el-card><div class="stat-num">{{ overview.project_count }}</div><div class="stat-label">项目总数</div></el-card>
      </el-col>
    </el-row>

    <el-card style="margin-bottom: 16px">
      <div class="filters">
        <el-select v-model="projectId" placeholder="全部项目" clearable style="width: 220px" @change="loadChart">
          <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-radio-group v-model="granularity" @change="loadChart">
          <el-radio-button value="day">按天</el-radio-button>
          <el-radio-button value="hour">按小时</el-radio-button>
        </el-radio-group>
        <el-select v-model="days" style="width: 130px" @change="loadChart">
          <el-option label="最近 24 小时" :value="1" />
          <el-option label="最近 3 天" :value="3" />
          <el-option label="最近 7 天" :value="7" />
          <el-option label="最近 30 天" :value="30" />
          <el-option label="最近 90 天" :value="90" />
        </el-select>
      </div>
      <div ref="chartRef" style="height: 360px"></div>
    </el-card>

    <el-card>
      <template #header>项目访问排行</template>
      <el-table :data="overview.top_projects" stripe>
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="name" label="项目名称" />
        <el-table-column prop="visits" label="访问量" width="140" align="center" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import api, { errMsg } from '../api'

const loading = ref(false)
const overview = ref({ total_visits: 0, today_visits: 0, project_count: 0, top_projects: [] })
const projects = ref([])
const projectId = ref(null)
const granularity = ref('day')
const days = ref(7)
const chartRef = ref()
let chart = null

async function loadOverview() {
  try {
    const { data } = await api.get('/stats/overview')
    overview.value = data
    const { data: list } = await api.get('/projects')
    projects.value = list
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}

async function loadChart() {
  loading.value = true
  try {
    const params = { granularity: granularity.value, days: days.value }
    if (projectId.value) params.project_id = projectId.value
    const { data } = await api.get('/stats/series', { params })
    await nextTick()
    if (!chart && chartRef.value) {
      chart = echarts.init(chartRef.value)
      window.addEventListener('resize', () => chart?.resize())
    }
    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 30, bottom: 40 },
      xAxis: {
        type: 'category',
        data: data.map((d) => d.bucket.slice(5, granularity.value === 'hour' ? 16 : 10)),
        axisLabel: { rotate: granularity.value === 'hour' ? 45 : 0 },
      },
      yAxis: { type: 'value', minInterval: 1 },
      series: [
        {
          name: '访问量',
          type: 'line',
          smooth: true,
          data: data.map((d) => d.count),
          areaStyle: { opacity: 0.15 },
          itemStyle: { color: '#409eff' },
        },
      ],
    })
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadOverview()
  loadChart()
})

onBeforeUnmount(() => {
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.cards { margin-bottom: 16px; }
.stat-num { font-size: 32px; font-weight: 700; color: #303133; }
.stat-label { color: #909399; margin-top: 4px; }
.filters { display: flex; gap: 16px; margin-bottom: 12px; align-items: center; }
</style>
