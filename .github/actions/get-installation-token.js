const { createAppAuth } = require("@octokit/auth-app");

(async () => {
  console.log("HEEERE", {
    appId: process.env.GH_APP_ID,
    privateKey: process.env.GH_APP_PRIVATE_KEY,
    installationId: process.env.GH_APP_INSTALLATION_ID,
  });
  const auth = createAppAuth({
    appId: process.env.GH_APP_ID,
    privateKey: process.env.GH_APP_PRIVATE_KEY,
  });

  const resp = await auth({
    type: "installation",
    installationId: process.env.GH_APP_INSTALLATION_ID,
  });
  console.log(resp.token);
  return resp.token;
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
