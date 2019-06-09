from sanic import Sanic, response
from MaterialPlanning import MaterialPlanning

app = Sanic()

app.static('/', './ArkPlannerWeb/index.html')

@app.route("/plan", methods=['POST'])
async def plan(request):
    try:
        input_data = request.json
        owned_dct = input_data["owned"]
        required_dct = input_data["required"]
    except:
        return response.json({"error": True, "reason": "Uninterpretable input"})

    try:
        mp = MaterialPlanning()
        dct = mp.get_plan(required_dct, owned_dct, False)
    except ValueError as e:
        return response.json({"error": True, "reason": str(e)})

    return response.json(dct)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
