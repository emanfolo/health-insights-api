import * as functions from "firebase-functions";
import * as admin from "firebase-admin";

export const ensureUserProfile = functions.auth
  .user()
  .onCreate(async (user) => {
    const userRef = admin.firestore().doc(`users/${user.uid}`);

    const snapshot = await userRef.get();

    if (!snapshot.exists) {
      // The user document doesn't exist, so we create it.
      // This might be the case if the client-side operation failed.
      return userRef.set({
        uid: user.uid,
        displayName: user.displayName || "Anonymous",
        photoURL:
          user.photoURL ||
          "https://avatars.githubusercontent.com/u/214020?s=40&v=4",
        lastLogin: admin.firestore.FieldValue.serverTimestamp(),
      });
    } else {
      return userRef.update({
        lastLogin: admin.firestore.FieldValue.serverTimestamp(),
      });
    }
  });

export const cleanupUserData = functions.auth.user().onDelete(async (user) => {
  const uid = user.uid;
  try {
    const userRef = admin.firestore().collection("users").doc(uid);
    await userRef.delete();
    console.log(`Deleted user data for user: ${uid}`);
  } catch (error) {
    console.error(`Error cleaning up user data for user: ${uid}`, error);
  }
});
