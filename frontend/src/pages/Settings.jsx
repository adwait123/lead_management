import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

export function Settings() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-2">Manage your application settings</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Demo Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Reset Demo Data</h3>
            <p className="text-sm text-gray-500 mb-4">
              Reset all data to default demo state
            </p>
            <Button variant="destructive">Reset Demo Data</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}