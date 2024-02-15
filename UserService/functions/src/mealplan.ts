import * as functions from "firebase-functions";
import * as admin from "firebase-admin";

export const saveMealplan = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError(
      "unauthenticated",
      "The user must be authenticated to delete a like.",
    );
  }

  const userId = context.auth.uid;
  const {mealplan} = data;

  const userMealplanRef = admin
    .firestore()
    .collection("users")
    .doc(userId)
    .collection("savedMealplans")
    .doc();

  await userMealplanRef.set({
    ...mealplan,
    createdAt: admin.firestore.FieldValue.serverTimestamp(),
  });
});

export const unsaveMealplan = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError(
      "unauthenticated",
      "The user must be authenticated to delete a like.",
    );
  }

  const userId = context.auth.uid;
  const {mealplanId} = data;

  try {
    await admin
      .firestore()
      .collection("users")
      .doc(userId)
      .collection("savedMealplans")
      .doc(mealplanId)
      .delete();
    console.log(`Mealplan ${mealplanId} removed successfully.`);
  } catch (error) {
    console.error(`Error removing mealplan: ${error}`);
  }
});
