<template>
  <router-view v-if="isLogin" />
  <el-container v-else style="height: 100vh">
    <el-header class="header">
      <div class="brand">原型展示平台</div>
      <el-menu mode="horizontal" router :default-active="activeMenu" :ellipsis="false" class="menu">
        <el-menu-item index="/">项目管理</el-menu-item>
        <el-menu-item index="/stats">访问统计</el-menu-item>
      </el-menu>
      <el-dropdown @command="onCommand">
        <span class="user">{{ username }} ▾</span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="pwd">修改密码</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </el-header>
    <el-main style="background: #f5f7fa">
      <router-view />
    </el-main>

    <el-dialog v-model="pwdVisible" title="修改密码" width="400px">
      <el-form label-width="80px">
        <el-form-item label="原密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="pwdForm.confirm" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" @click="changePwd">确定</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api, { errMsg } from './api'

const route = useRoute()
const router = useRouter()
const isLogin = computed(() => route.path === '/login')
const activeMenu = computed(() => route.path)
const username = ref(localStorage.getItem('username') || 'admin')

const pwdVisible = ref(false)
const pwdForm = reactive({ old_password: '', new_password: '', confirm: '' })

function onCommand(cmd) {
  if (cmd === 'logout') {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    router.push('/login')
  } else if (cmd === 'pwd') {
    pwdForm.old_password = ''
    pwdForm.new_password = ''
    pwdForm.confirm = ''
    pwdVisible.value = true
  }
}

async function changePwd() {
  if (pwdForm.new_password !== pwdForm.confirm) {
    ElMessage.error('两次输入的新密码不一致')
    return
  }
  try {
    await api.put('/auth/password', {
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    pwdVisible.value = false
    localStorage.removeItem('token')
    router.push('/login')
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}
</script>

<style>
body { margin: 0; font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; }
.header {
  display: flex; align-items: center; gap: 24px;
  border-bottom: 1px solid #e4e7ed; background: #fff;
}
.brand { font-size: 18px; font-weight: 700; color: #409eff; white-space: nowrap; }
.menu { flex: 1; border-bottom: none !important; }
.user { cursor: pointer; color: #606266; font-size: 14px; }
</style>
